import numpy as np
from matplotlib.animation import FuncAnimation

import matplotlib.pyplot as plt
from matplotlib import animation

import signal as sg


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


class Animation:
    """
    Support a Matplotlib animation
    inspired on http://jakevdp.github.io/blog/2012/08/18/matplotlib-animation-tutorial/
    """

    def animate(self, _):
        """
        Animation function. This is called sequentially
        :param _:
        :return:
        """
        # if self.debug:
        #    self.watch.start()

        patches = self.provider.animated_patches(self.ax, self.text)
        # if self.debug:
        #    print('   animation time: %s' % self.watch.current_duration())
        return patches

    def __init__(self, provider, figure, win_size, text_position, title='Animation', interval=83, show_animation=True,
                 save_after=0, debug=False, show_plot=True):
        """
        Init
        :param provider: is an object that must implement .add_fixes_patches and .animated_patches
        :param win_size:
        :param text_position:
        :param title:
        :param interval:
        :param show_animation:
        :param save_after:
        :param debug:
        :param show_plot:
        """
        self.provider   = provider
        self.title      = title
        self.save_after = save_after  # save animation after x animations (0 means never save)
        self.debug      = debug
        # self.watch      = sg.StopWatch()

        if show_animation:
            if show_plot is False:
                plt.switch_backend('agg')
            # First set up the figure, the axis, and the plot element we want to animate
            # self.provider.fig = plt.figure()
            # self.provider.gcf = plt.gcf()
            # self.provider.gcf.canvas.set_window_title(self.title)
            xlim = (win_size[0], win_size[1])
            ylim = (win_size[2], win_size[3])
            self.ax = self.provider.main_window.fig_view.axes

            tx, ty    = text_position
            self.text = self.ax.text(tx, ty, '', transform=self.ax.transAxes)

            # fixes patches
            self.provider.add_fixes_patches(self.ax)
            # Use adjustable='box-forced' to make the plot area square-shaped as well.
            self.ax.set_aspect('equal', adjustable='datalim')

            # call the animator.  blit=True means only re-draw the parts that have changed.
            frames = 2000 if self.save_after == 0 else self.save_after
            anim = animation.FuncAnimation(figure, self.animate, frames=frames, init_func=init,
                                           interval=interval, blit=True)

            if self.save_after > 0:
                name = '../Videos/%s.mp4' % self.title
                anim.save(name, fps=30, extra_args=['-vcodec', 'libx264'])
                print('    **** saved %s' % name)

            if show_plot is True:
                plt.show()
                pass
            else:
                _ = plt.figure()

def init():
    """
    Initialization function: plot the background of each frame
    :return: list
    """
    return []
