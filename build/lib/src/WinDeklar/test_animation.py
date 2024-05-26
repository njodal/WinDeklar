import sys
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

import WinDeklar.signal_aux as sg


class RealTimeGraph:
    def __init__(self, fig, data_provider, min_x=-1, repeat_length=50, frames=None, interval=100):
        self.repeat_length = repeat_length
        self.data_provider = data_provider if isinstance(data_provider, list) else [data_provider]

        # Create an axis in the given figure
        self.ax = fig.add_subplot(111)
        self.lines = []
        for dp in self.data_provider:
            line, = self.ax.plot([], [], color=dp.color)
            self.lines.append([line, dp, sg.SignalHistory(self.repeat_length), sg.SignalHistory(self.repeat_length)])

        # Set the axis limits
        self.ax.set_xlim(min_x, self.repeat_length)
        min_y = None
        max_y = None
        for dp in self.data_provider:
            min_y1, max_y1 = dp.get_bounds()
            if min_y is None or min_y1 < min_y:
                min_y = min_y1
            if max_y is None or max_y1 > max_y:
                max_y = max_y1
        self.ax.set_ylim(min_y, max_y)

        self.anim = FuncAnimation(fig, self.update_frame, frames=frames, interval=interval, blit=False)

    def update_frame(self, frame):
        for [line, dp, xs, ys] in self.lines:
            x, y = dp.get_next_values(frame)
            # print(' frame:%s x:%s y:%s' % (frame, x, y))
            xs.append(x)
            ys.append(y)

            x_max = xs.max()
            if x_max > self.repeat_length:
                self.ax.set_xlim(x_max - self.repeat_length, x_max)
            line.set_data(xs.values, ys.values)


class RealTimeDataProvider(object):
    def __init__(self, min_y=0.0, max_y=10.0, color='Red'):
        self.min_y = min_y
        self.max_y = max_y
        self.color = color

    def get_bounds(self):
        return self.min_y, self.max_y

    def get_min_y(self):
        return self.min_y

    def get_max_y(self):
        return self.max_y

    def get_next_values(self, i):
        return i, i


class RealTimeRandomDataProvider(RealTimeDataProvider):
    def __init__(self, min_y=0.0, max_y=10.0, color='Red'):
        super(RealTimeRandomDataProvider, self).__init__(min_y=min_y, max_y=max_y, color=color)

    def get_next_values(self, i):
        return i, np.random.uniform(self.min_y, self.max_y)


class RealTimeFunctionDataProvider(RealTimeDataProvider):
    def __init__(self, min_y=-1.2, max_y=1.2,function=np.sin, inc=np.radians(10), color='Red'):
        self.function = function
        self.inc      = inc
        self.last_r   = 0.0
        super(RealTimeFunctionDataProvider, self).__init__(min_y=min_y, max_y=max_y, color=color)

    def get_next_values(self, i):
        y = self.function(self.last_r)
        self.last_r += self.inc
        return i, y


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("Animated Graph")

        # Create a Matplotlib figure
        fig = plt.figure()

        # Create an instance of CustomAnimation and pass the figure
        provider = [RealTimeFunctionDataProvider(function=np.sin, color='Blue'),
                    RealTimeFunctionDataProvider(function=np.cos, color='Red'),
                    RealTimeRandomDataProvider(min_y=-1, max_y=1, color='Orange')]
        self.animation = RealTimeGraph(fig, provider)

        # Create a Matplotlib canvas to display the animation
        canvas = FigureCanvas(fig)

        # Add the canvas to the vertical layout
        layout = QVBoxLayout()
        layout.addWidget(canvas)

        # Create a widget to hold the layout
        widget = QWidget(None)
        widget.setLayout(layout)

        # Set the widget as the central content of the main window
        self.setCentralWidget(widget)

        # Start the animation
        # self.animation._start()

        # Show the main window
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
