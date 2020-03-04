import sys
import random

from functools import partial

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QSpinBox, QLabel, QRadioButton,\
    QErrorMessage, QMainWindow, QFormLayout, QWidget
from PySide2.QtCore import QFile, QObject, QRegExp

from matplotlib.backends.qt_compat import QtCore, QtWidgets 
from matplotlib.backends.backend_qt5agg import (FigureCanvas, 
                                                NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

from plotter import Plotter

class MissingParameter(BaseException):
    pass

class MyMainWindow(QMainWindow):

    def __init__(self):
        super(MyMainWindow, self).__init__()
        self.form_widget = QFormLayout(self)
        self.plotter = DiceRoller('ui/MainWindow.ui')
        self.setCentralWidget(self.plotter)

class DiceRoller(QtWidgets.QWidget):
    
    def __init__(self, ui_file, parent=None):
        super(DiceRoller, self).__init__(parent)
        #load ui file
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        #startup
        self.plotter = Plotter(parent=self)
        self.window.mainLayout.addWidget(self.plotter)
        self.setup_ui()
        self.window.show()
        
    def setup_ui(self):
        #some useful things
        self.all_spin_boxes = self.window.findChildren(QSpinBox, QRegExp('.*'))
        self.dice_spin_boxes = self.window.findChildren(QSpinBox, 
                                                   QRegExp('^d[0-9]{1,3}SpinBox$'))
        self.other_spin_boxes = [s for s in self.all_spin_boxes
                                if s not in self.dice_spin_boxes]
        self.labels = self.window.findChildren(QLabel, QRegExp('[A-z]*Value'))
        self.radio_buttons = self.window.findChildren(QRadioButton, 
                                                      QRegExp('[A-z]*Button'))
        self.connect_items()
        global debug
        if debug:
            self.__run_mini_test()
        
    def __run_mini_test(self):
            from PySide2 import QtTest 
            from PySide2.QtCore import Qt
            self.window.d4SpinBox.setValue(4)
            self.window.d4RadioButton.setChecked(True)
            self.window.eachAddSpinBox.setValue(0)
            QtTest.QTest.mouseClick(self.window.runButton, Qt.LeftButton)
    
    def connect_items(self):
        self.window.runButton.clicked.connect(self.run)
        self.window.resetButton.clicked.connect(self.reset_ui)
        for s in self.dice_spin_boxes:
            a = partial(self.reset_other_spinboxes, s)
            s.valueChanged.connect(self.reset_other_spinboxes)
    
    def reset_ui(self):
        for s in self.all_spin_boxes:
            s.setValue(0)
        for l in self.labels:
            l.setText('N/A')
        for b in self.radio_buttons:
            b.setAutoExclusive(False) #otherwise I cannot uncheck and I really want to...
            b.setChecked(False)
            b.setAutoExclusive(True)
                
    def reset_other_spinboxes(self):
        caller = self.sender()
        for s in self.dice_spin_boxes:
            if s is not caller:
                s.blockSignals(True) #otherwise it will emit and trigger an infinite recursion
                s.setValue(0)
                s.blockSignals(False)
        
    def run(self):
        try:
            n_of_dice, type_of_die, to_add_each, to_add_total = (self.get_parameters())
        except MissingParameter:
            return
        rolls = self.run_simulation(n_of_dice, type_of_die, to_add_each, to_add_total)
        self.plot(rolls)
    
    def get_parameters(self):
        for s in self.dice_spin_boxes:
            if s.value():
                n_of_dice = s.value()
                type_of_die = int(s.objectName().replace('d','').replace('SpinBox',''))
                break #we have a method to make sure that there is only one box that is non-zero
        else:
            self.popup_error('Please choose how many dice you want to roll')
            raise MissingParameter
        for b in self.radio_buttons:
            if b.isChecked():
                break
        else:
            self.popup_error('Please choose a type of die to roll')
            raise MissingParameter
        to_add_total = self.window.totalAddSpinBox.value()
        to_add_each = self.window.eachAddSpinBox.value()
        return n_of_dice, type_of_die, to_add_each, to_add_total
    
    def run_simulation(self, n_of_dice, type_of_die, to_add_each, to_add_total,
                       simulate=100000):
        rolls = []
        for i in range(simulate):
            total = 0
            for k in range(n_of_dice):
                total += random.randint(1,type_of_die) + to_add_each
            rolls.append(total + to_add_total)
        print(f'Rolled {n_of_dice}d{type_of_die} + {to_add_each}, adding {to_add_total} to the total')
        print(f'Obtaining an average of {sum(rolls)/100000}')
        print(f'With minimum {min(rolls)} and maximum {max(rolls)}')
        return rolls
    
    def popup_error(self, msg):
        popup = QErrorMessage()
        popup.setModal(True)
        popup.showMessage(msg)
        popup.exec_()
        
    def plot(self, rolls):
        self.plotter.plot(rolls)
        

if __name__ == "__main__":
    debug = True
    app = QApplication(sys.argv)
    window = MyMainWindow()
#     sys.exit(app.exec_())
    app.exec_()