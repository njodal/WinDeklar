#!/usr/bin/env python

# just a testbed to experiment with matplotlib, pyqt and so on, useful when changing version of one of them

import sys
import random

from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.lines as mlines
import matplotlib.pyplot as plt


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=1, height=1, x_lower=0, x_upper=50, y_lower=1, y_upper=6, x_visible=True,
                 y_visible=True):
        figure = Figure(figsize=(width, height))
        self.x_lower, self.x_upper = [x_lower, x_upper]
        self.y_lower, self.y_upper = [y_lower, y_upper]
        self.x_visible, self.y_visible = [x_visible, y_visible]
        self.axes = figure.add_subplot(111)
        self.set_axis()

        FigureCanvas.__init__(self, figure)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.update_figure()
        # timer = QtCore.QTimer(self)
        # timer.timeout.connect(self.update_figure)
        # timer.start(1000)

    def set_axis(self):
        self.axes.axis('scaled')
        # We want the axes cleared every time plot() is called
        # self.axes.hold(False)
        self.axes.set_xbound(lower=self.x_lower-10, upper=self.x_upper)
        self.axes.set_ybound(lower=self.y_lower, upper=self.y_upper+5)
        self.axes.get_xaxis().set_visible(self.x_visible)
        self.axes.get_yaxis().set_visible(self.y_visible)

    def update_figure(self):
        self.axes.clear()
        self.set_axis()
        old_x, old_y = [self.x_lower, 0]
        for x in range(self.x_lower+1, self.x_upper):
            y = random.randint(self.y_lower, self.y_upper)
            line = mlines.Line2D([old_x, x], [old_y, y])
            self.axes.add_line(line)
            old_x, old_y = [x, y]

        show_arrow(self.axes, [0, 0], [5, 5])
        rectangle = plt.Rectangle((2, 2), 1, 10, angle=60, alpha=0.5)
        self.axes.add_patch(rectangle)

        self.draw()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, win_title='Test window', width=1, height=1):
        QtWidgets.QMainWindow.__init__(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)  # Garbage-collect the window after it's been closed.
        self.setWindowTitle(win_title)

        main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(main_widget)

        box_layout = QtWidgets.QVBoxLayout(main_widget)

        canvas = MplCanvas(main_widget, width=width, height=height)
        box_layout.addWidget(canvas)

        self.show()


def show_arrow(ax, p1, p2, color='Black', connectionstyle='arc3,rad=0.3'):
    ax.annotate("", xy=p1, xycoords='data', xytext=p2, textcoords='data',
                arrowprops=dict(arrowstyle="->", color=color, shrinkA=5, shrinkB=5, patchA=None, patchB=None,
                                connectionstyle=connectionstyle,
                                ),
                )


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    title = 'Test if PtQt is working, should draw a graph and a rectangle'
    app_window = MainWindow(win_title=title, width=15, height=10)
    sys.exit(app.exec_())
