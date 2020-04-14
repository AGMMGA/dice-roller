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
        step = (max(distribution) - min(distribution)) // 25 + 1
        ticks = range(min(distribution), max(distribution)+2, step)
        counts = Counter(distribution)
        percents = [(i,j/len(distribution)) 
                    for i,j in counts.items()]
        percents.sort(key=lambda x: x[0])
        percents = np.array(percents)
#         heights = np.histogram(distribution[], bins=ticks)
#         percent = [i/sum(heights)*100 for i in heights]
        ax.bar(percents[:,0], percents[:,1], 
               align='center')
        #the ticks are ugly for number higher than 100, 
        #but axes.set_xticks() has no rotation option...
        ax.set_xticks(ticks)
        self.static_canvas.draw()
        self.static_canvas.show()
        self.called = True 
        
if __name__ == "__main__":
    raise NotImplementedError('Do not run this file as main')