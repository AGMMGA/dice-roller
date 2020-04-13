import numpy as np
import time

from collections import Counter

from matplotlib.backends.qt_compat import QtCore, QtWidgets 
from matplotlib.backends.backend_qt5agg import (FigureCanvas, 
                                                NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

from PySide2 import QtWidgets, QtCore



class Plotter(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super(Plotter, self).__init__(parent=parent)
        self.called = False
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )
        self.layout = QtWidgets.QVBoxLayout(self)
        self.static_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.layout.addWidget(self.static_canvas)
        
    def plot(self, distribution):
#         counts = tuple(Counter(distribution))
#         print(counts)
        if self.called:
            self.static_canvas.figure.clf()
            color='black'
        ax = self.static_canvas.figure.subplots()
        plt = ax.hist(distribution)
#         plt = ax.plot(x,y)
        self.static_canvas.draw()
        self.static_canvas.show()
        self.called = True 
        
if __name__ == "__main__":
    raise NotImplementedError('Do not run this file as main')