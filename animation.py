
import matplotlib.pyplot as plt
from matplotlib import animation


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
