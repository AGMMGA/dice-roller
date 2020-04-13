import sys
import random

from collections import Counter
from functools import partial

import numpy as np

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
            self.window.eachAddSpinBox.setValue(1)
            self.window.totalAddSpinBox.setValue(2)
            QtTest.QTest.mouseClick(self.window.runButton, Qt.LeftButton)
    
    def connect_items(self):
        self.window.runButton.clicked.connect(self.run)
        self.window.resetButton.clicked.connect(self.reset_ui)
        for s in self.dice_spin_boxes:
#             a = partial(self.reset_other_spinboxes, s)
            a = self.__identify_yourself() #generates a fake call, so that we can identify who is the event sender
            s.valueChanged.connect(self.reset_other_spinboxes)
        for s in self.radio_buttons:
            a = self.__identify_yourself()
            s.clicked.connect(self.reset_spinboxes_after_radio_click)
        
    def __identify_yourself(self):
        return 
    
    def reset_ui(self):
        for s in self.all_spin_boxes:
            s.setValue(0)
        for l in self.labels:
            l.setText('N/A')
        for b in self.radio_buttons:
            b.setAutoExclusive(False) #otherwise I cannot uncheck and I really want to...
            b.setChecked(False)
            b.setAutoExclusive(True)
            
    def reset_spinboxes_after_radio_click(self):
        '''
        When a radio button is clicked, it resets all spinboxes to 0
        except for the spinbox corresponding to the radio button, which is set to 1
        if its value is zero, or untouched if it has already a value.
        '''
        caller = self.sender()
        sister_spinbox_name = caller.objectName().replace('RadioButton', 'SpinBox')       
        for s in self.dice_spin_boxes:
            if s.objectName() == sister_spinbox_name and s.value():
                continue
            elif s.objectName() == sister_spinbox_name:
                s.setValue(1)
            else:
                s.setValue(0)
                
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
        rolls, mean, mode, median = self.run_simulation(
            n_of_dice, type_of_die, to_add_each, to_add_total)
        self.window.meanValue.setText(str(mean))
        self.window.modeValue.setText(str(mode))
        self.window.medianValue.setText(str(median))
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
    
    def roll(self, type_of_die, to_add_each):
        return random.randint(1,type_of_die) + to_add_each
    
    def run_simulation(self, n_of_dice, type_of_die, to_add_each, to_add_total,
                       simulate=1000000):
        '''
        Performs <simulate> rolls of: 
        (<n_of_dice>d<type_of_dice> + <to_add_each>) + <to_add_total>
        e.g. 
        (3d6 + 1) + 4: roll a six-faced die 3 times, add 1 to each roll and
        add 4 to the grand total
        '''
        #roll all the dice separately
        rolls = np.random.randint(1 + to_add_each, #min 
                                  type_of_die + 1 + to_add_each, #max
                                  simulate*n_of_dice) #total rolls
        #create roll groups of n_of_dice
        rolls = np.reshape(rolls, (simulate, n_of_dice))
        #sum each roll group
        rolls = np.sum(rolls, axis=1)
        #include to_add_total
        if to_add_total:
            x = np.array([to_add_total]*simulate)
            rolls = rolls + x
        mean = np.mean(rolls)
        median = np.median(rolls)
        # mode calculation is in scipy, but adding a dependence for one function is silly
        counts = Counter(rolls)
        #Below is a mouthful to get the key with the highest value. Ugly, but I don't care right now
        mode = list(counts.keys())[list(counts.values()).index(max(counts.values()))]
        print(f'Rolled {n_of_dice}d{type_of_die} + {to_add_each}, adding {to_add_total} to the total')
        print(counts)
        return rolls, mean, mode, median
    
    def popup_error(self, msg):
        popup = QErrorMessage()
        popup.setModal(True)
        popup.showMessage(msg)
        popup.exec_()
        
    def plot(self, rolls):
        self.plotter.plot(rolls)
        

if __name__ == "__main__":
    debug = 1
    app = QApplication(sys.argv)
    window = MyMainWindow()
#     sys.exit(app.exec_())
    app.exec_()