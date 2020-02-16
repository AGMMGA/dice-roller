import sys
import random

from functools import partial

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QSpinBox, QLabel, QRadioButton,\
    QErrorMessage, QMessageBox
from PySide2.QtCore import QFile, QObject, QRegExp
from PySide2 import QtGui

class MissingParameter(BaseException):
    pass

class DiceRoller(QObject):
    
    def __init__(self, ui_file, parent=None):
        super(DiceRoller, self).__init__(parent)
        #load ui file
        ui_file = QFile('ui/MainWindow.ui')
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        #startup
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
        for i in range(n_of_dice*simulate):
            rolls.append((random.randint(1,type_of_die) + to_add_each)
                        + to_add_total)
        return rolls
    
    def popup_error(self, msg):
        popup = QErrorMessage()
        popup.setModal(True)
        popup.showMessage(msg)
        popup.exec_()
        
    def plot(self):
        pass
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiceRoller('ui/MainWindow.ui')
    sys.exit(app.exec_())