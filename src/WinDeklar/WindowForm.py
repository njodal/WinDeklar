#!/usr/bin/env python
import functools
import sys
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib import animation
from PyQt5 import QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import WinDeklar.points_box as pb
import WinDeklar.QTAux as QTAux
import WinDeklar.record as rc
import WinDeklar.signal_aux as sg
import WinDeklar.yaml_functions as yaml


def run_winform(form_file_path, provider, ext='yaml'):
    """
    Given the file path of the program that handle the form logic, loads and exec the corresponding WinForm
    :param form_file_path: most common value is __file__
    :param provider:       subclass of HostModel
    :param ext:            extension of the WinForm definition
    :return:
    """
    win_config_name = yaml.get_file_name_with_other_extension(form_file_path, ext)
    ConfigurableWindow(win_config_name, provider)


class ConfigurableWindow(QtWidgets.QMainWindow):
    """
    Defines a WinForm with many components inside in a declarative manner in a config file
    Notes:
        - a config_file_name is a yaml that has the definition (see view_example.yaml)
        - a typical windows has some widgets in the left and a Figure in the right (like a graph or a map)
    """

    def __init__(self, config_file_name, provider):
        """
        Init
        :param config_file_name: name of the file containing the window definition
        :param provider: handles all the form logic, usually a subclass of HostModel
        """
        super(ConfigurableWindow, self).__init__(parent=None)

        self.widgets   = []
        self.fig_views = []
        self.provider  = provider
        self.provider.set_main_window(self)

        self.win_config = get_win_config(config_file_name)

        # status bar logic
        self.statusbar    = create_status_bar(self.win_config, self)
        self.progress_bar = GeneralProgressBar(widget=self.statusbar, stretch=1, visible=False)

        # menu bar
        menu_bar = create_menu_bar(self.win_config, self, self.provider)
        if menu_bar is not None:
            self.setMenuBar(menu_bar)

        # toolbar
        toolbar, toolbar_widgets = create_toolbar(self.win_config, self, self.provider)
        if toolbar is not None:
            self.widgets.extend(toolbar_widgets)
            self.addToolBar(toolbar)

        # Define the geometry of the main window
        size = self.win_config.get('size', [300, 300, 300, 300])
        QTAux.set_window(self, get_title(self.win_config, self.provider), size)

        # Create FRAME
        self.FRAME = QtWidgets.QFrame(self)
        if 'back_color' in self.win_config:
            [c1, c2, c3, c4] = self.win_config['back_color']
            self.FRAME.setStyleSheet("QWidget { background-color: %s }" % QtGui.QColor(c1, c2, c3, c4).name())
        self.LAYOUT   = QtWidgets.QGridLayout()
        self.fig_views, layout_widgets = set_layout(self.LAYOUT, self.win_config.get('layout', []), self,
                                                    row_col=[0, 0])
        self.widgets.extend(layout_widgets)
        self.FRAME.setLayout(self.LAYOUT)
        self.setCentralWidget(self.FRAME)

        self.provider.initialize()
        self.refresh()
        self.show()

    def get_value(self, name):
        """
        Returns the value of a state variable
        :param name: name of the variable
        :return:
        """
        # print('get value for %s' % name)
        return self.provider.get_value(name)

    def widget_has_value(self, name):
        return self.provider.widget_has_value(name)

    def set_widget_value(self, name, value):
        self.provider.set_value(name, value)
        self.refresh_other_widgets(name)
        self.refresh()

    def set_widget_min_max(self, widget_name, min_value, max_value):
        widget = self.get_widget_by_name(widget_name)
        if widget is None:
            return
        widget.set_min_max(min_value, max_value)

    def set_widget_title(self, widget_name, new_title):
        widget = self.get_widget_by_name(widget_name)
        if widget is None:
            return
        widget.set_ename(new_title)

    def redraw_figures(self):
        [figure.draw() for figure in self.fig_views]

    def refresh(self):
        # initial values can be set before fig_view was created
        [figure.update_figure() for figure in self.fig_views]

    def refresh_widgets(self):
        for widget in self.widgets:
            widget.refresh()

    def refresh_widget(self, widget_name):
        widget = self.get_widget_by_name(widget_name)
        if widget is not None:
            widget.refresh()

    def refresh_other_widgets(self, widget_name):
        """
        If a widget that affect the value of others changed, it is needed to refresh all others'
            ex: if a combo of countries changes, the combo of cities must be reloaded
        :param widget_name:
        :return:
        """
        changed = self.get_widget_by_name(widget_name)
        if changed is not None and changed.refresh_others:
            # print('refresh others')
            for widget in self.widgets:
                if widget != changed:
                    widget.refresh()

    def get_widget_by_name(self, widget_name):
        for widget in self.widgets:
            if widget.name == widget_name:
                return widget
        return None

    def anim_is_running(self):
        for figure in self.fig_views:
            if figure.anim_is_running:
                return True
        return False

    def start_animations(self):
        [figure.start_animation() for figure in self.fig_views]

    def stop_animations(self):
        [figure.stop_animation() for figure in self.fig_views]

    def show_status_bar_msg(self, msg):
        if self.statusbar is None:
            print('No status bar defined')
            return
        self.statusbar.showMessage(msg)


class FigureView(FigureCanvas):
    """
    Display a drawing that responds to a change in widget values
    """
    name_key        = 'name'
    title_key       = 'title'
    subtype_key     = 'subtype'
    animation_key   = 'animation'
    x_axis_key      = 'x_axis'
    y_axis_key      = 'y_axis'
    axes_limits_key = 'axes_limits'
    text_pos_key    = 'text_position'

    def __init__(self, parent, config, size=(1, 1), scaled=True, x_visible=True, y_visible=True):

        self.parent   = parent
        self.subtype  = config.get(self.subtype_key, None)
        self.name     = config.get(self.name_key, 'no_name')
        title         = config.get(self.title_key, None)
        self.text_pos = config.get(self.text_pos_key, None)

        self.box_size    = pb.PointsBox()
        x_axis_def       = config.get(self.x_axis_key, {})
        self.x_axis_name = x_axis_def.get(self.name_key, None)
        y_axis_def       = config.get(self.y_axis_key, {})
        self.y_axis_name = y_axis_def.get(self.name_key, None)

        self.size_dim = size
        self.anim     = None
        width, height = self.size_dim
        self.figure   = Figure(figsize=None)  # not necessary to set figsize
        self.axes     = self.figure.add_subplot(111)

        if title is not None:
            self.figure.suptitle(title, fontsize='medium')

        axes_limits = config.get(self.axes_limits_key, None)
        if axes_limits is None:
            self.x_lower, self.x_upper = [-width, width]
            self.y_lower, self.y_upper = [-height, height]
        else:
            [self.x_lower, self.x_upper, self.y_lower, self.y_upper] = axes_limits

        self.x_visible, self.y_visible = [x_visible, y_visible]
        self.scaled = False if self.subtype == self.animation_key else scaled

        self.set_axis()

        FigureCanvas.__init__(self, self.figure)
        self.setParent(self.parent)

        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        # self.figure.tight_layout()
        self.figure.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9)

        self.figure.canvas.mpl_connect('button_press_event', self.onclick)
        self.figure.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

        dec         = 0.95
        self.text_x = - width * dec
        self.text_y = height  * dec

        # animation logic
        self.graph_lines   = None  # set to None to signal graph are not initialized yet
        self.data_provider = None
        self.graph_bounds  = None
        self.points_in_graph = 0
        self.anim_is_running = False
        if self.subtype == self.animation_key:
            interval, self.points_in_graph, self.graph_bounds, self.data_provider = \
                self.parent.provider.get_data_provider(self)
            if self.data_provider is None:
                raise Exception(
                    'Figure is defined as "animation" but not data provider is given, implement get_data_provider() '
                    'in provider ')
            self.anim = animation.FuncAnimation(self.figure, self.update_frame, frames=None, interval=interval,
                                                blit=False)

    # Drawing
    def clear(self):
        if self.anim is not None:
            # in case of animation do not change axes limits, anim itself does it
            return

        self.axes.clear()
        self.set_axis()

    def set_axis(self):
        if self.anim is not None:
            # in case of animation do not change axes limits, anim itself does it
            return

        if self.scaled:
            self.axes.axis('scaled')

        axes_limits = self.box_size.size() if not self.box_size.is_empty else None

        if axes_limits is not None:
            self.x_lower, self.x_upper, self.y_lower, self.y_upper = axes_limits
        self.axes.set_xbound(lower=self.x_lower, upper=self.x_upper)
        self.axes.set_ybound(lower=self.y_lower, upper=self.y_upper)
        self.axes.get_xaxis().set_visible(self.x_visible)
        self.axes.get_yaxis().set_visible(self.y_visible)

        ylabel_name = self.y_axis_name if self.y_axis_name is not None else ' '
        # assigning ' ' is a quick fix to assure y values fit in the figure
        self.axes.set_ylabel(ylabel_name)
        if self.x_axis_name is not None:
            self.axes.set_xlabel(self.x_axis_name)

    def resize_axis(self, points, fixed_points=(), with_reset=True, inc=1.1):
        """
        Recalculate the figure size with the given points and resize it
        :param points: :type list of [x, y]
        :param fixed_points: list of point to add in addition to points
        :param with_reset: whether to use the all points or just use the current ones
        :param inc:
        :return:
        """
        if with_reset:
            self.box_size.reset()
        self.box_size.add_points(points)
        self.box_size.add_points(fixed_points)
        self.box_size.set_bounds(self.axes, inc)

    def update_figure(self):
        self.clear()
        self.parent.provider.update_view(self, self.axes)
        self.parent.provider.apply_zoom()
        self.draw()

    def text_position(self):
        if self.text_pos is not None:
            return self.text_pos
        else:
            return [0, 0]

    def show_text(self, text_values, position=None):
        """
        Show a set of [name, value] in a given position on the graph
        useful to display summary info like test validity or current speed
        :param text_values: list of [name, value]
        :param position: position (x, y) to display the value, if not present the 'text_position' config value is used
        :return:
        """
        position1 = self.text_position() if position is None else position
        if position1 is None:
            return
        show_text_values(self.axes, text_values, position1[0], position1[1])

    # Events
    def onclick(self, event):
        self.parent.provider.on_mouse_click(event, self.axes, self)
        self.set_axis()
        self.draw()

    def on_mouse_move(self, event):
        if self.parent.provider.on_mouse_move(event, self.axes):
            self.set_axis()
            self.draw()

    def popup_context_menu(self, actions=(), update_figure=True):
        """
        Displays a contex menu
        :param actions: list of [name, event]
        :param update_figure: whether update the underlying figure after showing the menu, useful when an action
                              changes something, ex: in view_build_map changing the Wall position
        :return:
        """
        if len(actions) == 0:
            return
        context_menu = QTAux.Menu(self, actions=actions)
        context_menu.popup()
        if update_figure:
            self.update_figure()

    # Animation
    def update_frame(self, frame_number):
        # first time do initializations
        if self.graph_lines is None:
            self.initialize_graph_lines(self.graph_bounds, self.data_provider)

        self.anim_is_running = True
        # update graphs
        for [line, dp, xs, ys] in self.graph_lines:
            x, y = dp.get_next_values(frame_number)
            # print(' frame:%s x:%s y:%s' % (frame, x, y))
            xs.append(x)
            ys.append(y)

            x_max = xs.max()
            if x_max > self.graph_bounds[1]:
                self.axes.set_xlim(x_max - self.graph_bounds[1], x_max)
            line.set_data(xs.values, ys.values)

    def initialize_graph_lines(self, bounds, data_provider):
        """
        Initialize each of the graph lines
        :param bounds:
        :param data_provider:
        :return:
        """
        # Create a line for each data provider
        self.graph_lines = []
        for dp in data_provider:
            line, = self.axes.plot([], [], color=dp.color)
            xs = sg.SignalHistory(self.points_in_graph)
            ys = sg.SignalHistory(self.points_in_graph)
            self.graph_lines.append([line, dp, xs, ys])

        # Set the axis limits
        min_x, max_x     = bounds
        self.axes.set_xlim(min_x, max_x)
        min_y = None
        max_y = None
        for dp in self.data_provider:
            min_y1, max_y1 = dp.get_bounds()
            if min_y is None or min_y1 < min_y:
                min_y = min_y1
            if max_y is None or max_y1 > max_y:
                max_y = max_y1
        self.axes.set_ylim(min_y, max_y)

    def stop_animation(self):
        if self.anim is None:
            return
        self.anim.event_source.stop()
        self.anim_is_running = False

    def start_animation(self):
        if self.anim is None:
            return
        self.anim.event_source.start()
        self.anim_is_running = True


class SimpleFigure:
    """
    Provides the functionality to display a Window with a Figure inside
    Used mainly for displaying tests
    """

    def __init__(self, title='Figure', scaled=True, inc=1.0, size=(1, 1), adjust_size=True):
        plt.figure(title, figsize=size)
        self.ax = plt.subplot(111)
        if scaled:
            self.ax.axis('scaled')
        self.ax.set_xlim([-size[0], size[0]])
        self.ax.set_ylim([-size[1], size[1]])
        self.inc        = inc
        self.set_bounds = adjust_size
        self.box_size   = pb.PointsBox()

    def resize(self, points):
        self.box_size.add_points(points)

    def show(self):
        if self.set_bounds:
            self.box_size.set_bounds(self.ax, inc=self.inc)
        plt.show()


class Dialog(QtWidgets.QDialog):
    """
    Functionality for an Input Panel
    """

    def __init__(self, dialog_name, provider, default_size=(300, 300, 400, 400)):
        super(Dialog, self).__init__(parent=None)

        self.widgets   = []
        self.fig_views = []
        self.provider  = provider
        self.provider.set_main_window(self)

        self.win_config = get_win_config(dialog_name)

        # Define the geometry of the main window
        size = self.win_config.get('size', default_size)
        QTAux.set_window(self, get_title(self.win_config, self.provider), size)

        # Create FRAME
        self.FRAME  = QtWidgets.QFrame(self)
        self.LAYOUT = QtWidgets.QGridLayout()
        self.fig_views, self.widgets = set_layout(self.LAYOUT, self.win_config.get('layout', []), self, row_col=[0, 0])
        self.FRAME.setLayout(self.LAYOUT)

        self.provider.initialize()
        self.refresh()

    def show(self):
        self.exec_()

    def get_value(self, name):
        # print('get value for %s' % name)
        return self.provider.get_value(name)

    def widget_has_value(self, name):
        return self.provider.widget_has_value(name)

    def set_value(self, name, value):
        # print('%s changed to %s' % (name, value))
        self.provider.set_value(name, value)
        self.refresh_other_widgets(name)
        self.refresh()

    def refresh(self):
        [fig.update_figure() for fig in self.fig_views]

    def refresh_widgets(self):
        for widget in self.widgets:
            widget.refresh()

    def refresh_widget(self, widget_name):
        widget = self.get_widget_by_name(widget_name)
        if widget is not None:
            widget.refresh()

    def refresh_other_widgets(self, widget_name):
        # if a widget that affect the value of others changed, it is needed to refresh all others'
        #    ex: in view_color, the encoding combo changes the values of low and high sliders
        changed = self.get_widget_by_name(widget_name)
        if changed is not None and changed.refresh_others:
            # print('refresh others')
            for widget in self.widgets:
                if widget != changed:
                    widget.refresh()

    def get_widget_by_name(self, widget_name):
        for widget in self.widgets:
            if widget.name == widget_name:
                return widget
        return None

    def confirmed(self):
        # print('confirmed')
        self.close()


class HostModel(object):
    """
    Host for ConfigurableWindow
       provides all the methods need it by ConfigurableWindow (like state management and widget's definition)
    """

    def __init__(self, initial_values=None):
        # keys
        self.zoom_key = 'zoom'

        self._state      = initial_values if initial_values is not None else {}
        self.main_window = None

        self.zoom_center = None   # point where to center Zoom
        self.zoom_radius = 10.0   # radius around
        self.box_size    = pb.PointsBox()  # ToDo: only used in zoom, should be avoided

    def set_main_window(self, main_window):
        self.main_window = main_window

    def refresh(self):
        """
        Refresh the whole WinForm (widgets and figures)
        :return:
        """
        if self.main_window is None:
            return
        self.main_window.refresh_widgets()
        self.main_window.refresh()

    def refresh_figures(self):
        """
        Update all the figures in WinForm, useful when some change in the logic change the figure
        ex: when showing a map and a new path between two points in it is calculated
        :return:
        """
        if self.main_window is None:
            return
        self.main_window.redraw_figures()

    def refresh_widgets(self):
        """
        Refresh all widgets
        :return:
        """
        if self.main_window is None:
            return
        self.main_window.refresh_widgets()

    def refresh_widget(self, name):
        """
        Refresh just one widget
        :param name: widget name
        :return:
        """
        if self.main_window is None:
            return
        self.main_window.refresh_widget(name)

    def set_widget_min_max(self, name, min_value, max_value):
        """
        Set the min and max value of a given widget, useful for Slide when the min,max depends on other values
        :param name:
        :param min_value:
        :param max_value:
        :return:
        """
        if self.main_window is None:
            return
        self.main_window.set_widget_min_max(name, min_value, max_value)

    def set_widget_title(self, name, new_title):
        if self.main_window is None:
            return
        self.main_window.set_widget_title(name, new_title)

    def set_and_refresh_widget(self, widget_name, value):
        self._state[widget_name] = value
        self.refresh_widget(widget_name)

    def set_values(self, values):
        """
        Bulk update a set of values
        :param values: :type dictionary
        :return:
        """
        self._state.update(values)

    def set_value(self, name, value):
        """
        Set a new value for a state variable, if the
        :param name:
        :param value:
        :return:
        """
        self._state[name] = value
        self.widget_changed(name, value)
        self.refresh()

    def set_value_internal(self, name, value):
        """
        Set a new value for name without firing the widget_changed event
            Useful when the value is paired with an internal variable and because the slider rounds value some
            precision is lost (see self.orientation_key in view_localization.py for an example)
        :param name:    variable name
        :param value:
        :return: nothing
        """
        # print('%s changed to %s (internally)' % (name, value))
        self._state[name] = value

    def set_value_if_not_present(self, name, value):
        """
        Set variable value only if name is not already in state
        Useful for Label widgets, where the title is the initial value but later can be changed
        :param name:
        :param value:
        :return:
        """
        if name not in self._state:
            self.set_value(name, value)

    def widget_changed(self, name, value):
        """
        Event triggered when any widget changes its value, useful to set the values of other widgets
        Abstract method
        :param name:
        :param value:
        :return:
        """
        pass

    def get_widget_by_name(self, name):
        if self.main_window is None:
            return None
        return self.main_window.get_widget_by_name(name)

    def get_value(self, name, default=None):
        """
        Returns the value of a given variable
            cases:
                1. if it is already present in the _state it just return the value
                2. if it is calculated it does the math
                3. just return the default value
        :param name:
        :param default:
        :return:
        """
        if name in self._state:
            return self._state[name]
        else:
            calc_value = self.calculated_value(name)
            if calc_value is not None:
                return calc_value
            else:
                return default

    def widget_has_value(self, name):
        return name in self._state

    def widgets_def(self):
        """
        Abstract method
        used to programmatically define widgets instead of in the definition file
        :return:
        """
        # abstract method
        return []

    def initialize(self):
        """
        Called when the WinForm is loaded, useful for initialization stuff (like loading files)
        Abstract method
        :return:
        """
        pass

    def get_file_name(self, title='Open', file_filter='*.*', directory=''):
        """
        Returns a valid file name using the standard dialog
        :param title:        window title
        :param file_filter:  show file that comply with this filter only
        :param directory:    initial directory ('' means current one)
        :return: a file name (None means no file was chosen)
        """
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self.main_window, title, filter=file_filter,
                                                             directory=directory)
        return file_name if file_name != '' else None

    def get_file_name_to_save(self, title='Save', file_filter='*.*', directory=''):
        """
        Returns file name to be saved (can be a new one or an existing one
        :param title:
        :param file_filter:
        :param directory:
        :return:
        """
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self.main_window, title, filter=file_filter,
                                                             directory=directory)
        return file_name if file_name != '' else None

    def get_progress_bar(self):
        """
        Returns a progress bar to be displayed in the status bar
        :return:
        """
        # if main_windows is not set yet just return an empty one in order not to crash,
        # this it not a problem because main_window will be set later
        return self.main_window.progress_bar if self.main_window is not None else GeneralProgressBar()

    def title(self):
        """
        Returns the WinForm title
        :return: string or None (if None then the config title will be used)
        """
        return None

    def show_status_bar_msg(self, msg):
        if self.main_window is None:
            print('no main window defined yet')
            return
        self.main_window.show_status_bar_msg(msg)

    def update_view(self, figure, ax):
        """
        Update view of a given Figure
        Abstract method
        :param figure: name of the Figure
        :param ax:   axis of the Figure
        :return:
        """
        pass

    # Zoom management
    def zoom_active(self):
        return self._state.get(self.zoom_key, False)

    def get_zoom_actions(self, event):
        return [['Zoom in', functools.partial(self.set_zoom_in, event)], ['Zoom out', self.set_zoom_out]]

    def set_zoom_out(self):
        self._state[self.zoom_key] = False
        self.refresh()

    def set_zoom_in(self, event):
        self._state[self.zoom_key] = True
        self.zoom_center = [event.xdata, event.ydata]
        self.refresh()

    def toggle_zoom(self):
        self._state[self.zoom_key] = not self._state[self.zoom_key]
        if not self._state[self.zoom_key]:
            self.refresh()

    def set_zoom_center(self, event):
        if self.zoom_active():
            self.zoom_center = [event.xdata, event.ydata]
            self.refresh()

    def apply_zoom(self):
        if self.zoom_active() and self.zoom_center is not None:
            self.box_size.reset()
            self.box_size.add_points([[self.zoom_center[0] - self.zoom_radius, self.zoom_center[1] - self.zoom_radius],
                                      [self.zoom_center[0] + self.zoom_radius, self.zoom_center[1] + self.zoom_radius]])

    # events
    def on_mouse_click(self, event, ax, parent):
        # abstract method
        # print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
        #      ('double' if event.dblclick else 'single', event.button, event.x, event.y, event.xdata, event.ydata))
        if event.button == QTAux.MouseButton.Right:
            return self.on_right_click(event, ax, parent)
        else:
            return self.onclick(event, ax, parent)

    def onclick(self, event, ax, parent):
        # abstract method
        # print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
        #      ('double' if event.dblclick else 'single', event.button, event.x, event.y, event.xdata, event.ydata))
        pass

    def on_right_click(self, event, ax, parent):
        # abstract method
        # print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
        #      ('double' if event.dblclick else 'single', event.button, event.x, event.y, event.xdata, event.ydata))
        pass

    def on_mouse_move(self, event, ax):
        # abstract method
        # print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
        #      ('double' if event.dblclick else 'single', event.button, event.x, event.y, event.xdata, event.ydata))
        return False

    def calculated_value(self, name):
        """
        Abstract method, used to return a value that is a formula of other values'
        ex: a = b + c  so calculated_value of a = state[b] + state[c]
        :param name:
        :return:
        """
        # abstract method
        return None

    def save_cycle(self):
        """
        Save the info of a given cycle
        Note: it is directly called from an event in the UI (as defined in a yaml config file)
        :return:
        """
        file_name = 'cycle'
        r = rc.Record(file_name)
        to_store = self.get_info_to_save()
        r.write_group('cycle', to_store)
        print('File %s saved' % r.get_full_file_name())

    def get_info_to_save(self):
        # abstract method
        return {}

    # animation methods
    def get_data_provider(self, figure, interval=100, min_x=0.0, max_x=10.0, data_provider=None):
        """
        Abstract method
        :param figure:   :type FigureView
        :param interval: time at which show new data (in milliseconds)
        :param max_x:    max value in the x-axis, values greater than this will cause the graph to scroll left
        :param min_x:    start value for the x-axis
        :param data_provider:  subclass of RealTimeDataProvider (can be None)
        :return: interval (milliseconds), number of points to show, x axis bounds (ex: [-1, 100]), subclass of
                 RealTimeDataProvider (can be None)
        """
        dt            = interval/1000  # seconds
        max_points    = int(max_x/dt) + 1
        return interval, max_points, (min_x, max_x), data_provider

    def start_stop_animation(self):
        """
        Logit to start/stop the graph with only one button (who changes its title depending on the graph is
        running or not_
        :return:
        """
        if self.anim_is_running():
            self.stop_animation()
            is_running = False
        else:
            self.start_animation()
            is_running = True
        return is_running

    def anim_is_running(self):
        return self.main_window.anim_is_running()

    def stop_animation(self):
        self.main_window.stop_animations()

    def start_animation(self):
        self.main_window.start_animations()


class PropertiesHost(HostModel):
    """
    HostModel specialized for editing a set of properties (defined as a dict)
    """

    def __init__(self, dialog_name, properties):
        self.dialog_name   = dialog_name  # config name for the dialog
        self.properties    = properties
        self.changed       = {}
        self.was_confirmed = False

        self.status_msg = 'Show %s' % self.dialog_name
        initial_values = self.properties.copy()
        super(PropertiesHost, self).__init__(initial_values=initial_values)
        self.dialog = Dialog(self.dialog_name, self)

    def set_properties(self, properties):
        self.properties = properties

    def show(self):
        self.was_confirmed = False
        self.update_state()
        self.dialog.show()
        return self.changed

    def button_confirm(self):
        self.changed = self.get_changed()
        self.dialog.close()
        self.was_confirmed = True
        self.after_confirm(self.changed)

    def button_cancel(self):
        self.dialog.close()

    def after_confirm(self, changed):
        # abstract method
        pass

    def update_properties(self, changed):
        if changed is None:
            return
        self.properties.update(changed)

    def update_state(self):
        for k, v in self.properties.items():
            self.set_value(k, v)
            self.dialog.refresh_widget(k)

    def get_changed(self):
        changed = {}
        for k, v in self.properties.items():
            if k not in self._state or v == self._state[k]:
                continue
            changed[k] = self._state[k]
        return changed


class TestHost(HostModel):
    """
    HostModel specialized for showing a set of tests stored in a file.
        The file name and the test name must be defined in the .yaml config file
    """

    def __init__(self, initial_values):
        # keys
        self.test_key   = 'test'

        # test cases
        self.all_cases = []
        self.output    = None

        super(TestHost, self).__init__(initial_values=initial_values)

    def initialize(self):
        test_file_name = self.main_window.win_config.get('test_file_name', '')
        test_name      = self.main_window.win_config.get('test_name', '')
        test_file      = yaml.get_yaml_file(test_file_name)
        test           = yaml.get_record(test_file['general'], test_name, 'tests', 'test', alternative_key_name='call')
        self.all_cases = test['cases']
        self.set_widget_min_max(self.test_key, 0, len(self.all_cases) - 1)
        self.set_current_case()

    def widget_changed(self, name, _):
        if name == self.test_key:
            self.set_current_case()

    def set_current_case(self):
        case = self.get_current_case()
        if case is None:
            self.set_no_case()
            return

        current_case = case['case']
        self.output  = current_case.get('output', None)
        desc = self.set_case(current_case['input'],  self.output, current_case.get('desc', ''))
        self.show_status_bar_msg(desc)
        self.refresh_widgets()

    def get_current_case(self):
        if not self.all_cases:
            return None
        return self.all_cases[int(self._state[self.test_key])]

    def get_current_description(self, test_description):
        return test_description

    def set_case(self, case_input, output, description):
        """Abstract method for setting particular data"""
        return description

    def set_no_case(self):
        """Abstract method for setting null data when no case is ready"""
        pass


# Layout definition
def get_win_config(config_file_name, window_key='window'):
    config1 = yaml.get_yaml_file(config_file_name)
    win_config = config1.get(window_key, {})
    if win_config == {}:
        raise Exception('"window" keyword not present in config file %s' % config_file_name)
    return win_config


def get_title(win_config, provider, key='title'):
    title = provider.title()
    if title is None:
        title = win_config.get(key, 'Title')
    return title


def set_layout(father_layout, layout_config, window, row_col=None):
    fig_views = []
    widgets  = []
    if father_layout is None or not layout_config:
        return fig_views, widgets
    for sub_layout_config1 in layout_config:
        sub_layout_config = sub_layout_config1['item']
        sub_layout, fig_view_sub, sub_widgets = set_layout_items(father_layout, sub_layout_config, window, row_col)
        if fig_view_sub is not None:
            fig_views.append(fig_view_sub)
        widgets.extend(sub_widgets)
        fig_views1, widgets1 = set_layout(sub_layout, sub_layout_config.get('layout', []), window)
        fig_views.extend(fig_views1)
        widgets.extend(widgets1)
    return fig_views, widgets


def set_layout_items(father_layout, layout_config, window, row_col=None):
    fig_view    = None
    widgets     = []
    layout_type = layout_config['type']
    subtype     = layout_config.get('subtype', None)
    if layout_type == 'grid':
        layout, widgets = set_grid_layout(father_layout, subtype, layout_config, window, row_col=row_col)
    elif layout_type == 'figure':
        fig_view = set_figure_layout(father_layout, layout_config, window)
        layout   = None
    else:
        print('WARNING: layout type "%s" not implemented' % layout_type)
        layout = None
    return layout, fig_view, widgets


def set_grid_layout(father_layout, subtype, layout_config, window, row_col=None):
    if subtype == 'vertical':
        layout = QtWidgets.QVBoxLayout()
    elif subtype == 'horizontal':
        layout = QtWidgets.QHBoxLayout()
    else:
        raise Exception('Subtype %s not implemented for %s' % (subtype, type))
    widgets = add_widgets_to_window(layout, layout_config, window)
    if not row_col:
        father_layout.addLayout(layout)
    else:
        father_layout.addLayout(layout, row_col[0], row_col[1])

    fixed_width = layout_config.get('width', None)
    if fixed_width is not None:
        [widget.set_fixed_width(fixed_width) for widget in widgets]

    return layout, widgets


def set_figure_layout(father_layout, figure_config, window):
    fig_view = FigureView(window, figure_config)
    father_layout.addWidget(fig_view)
    return fig_view


def create_menu_bar(config, main_window, provider, key='menu_bar'):
    if key not in config:
        return None
    menu_bar = QtWidgets.QMenuBar(parent=main_window)
    menu_bar_config = config[key]
    for main_item1 in menu_bar_config:
        main_item = main_item1['item']
        main_menu = QtWidgets.QMenu(main_item['title'], main_window)
        menu_bar.addMenu(main_menu)
        if 'items' in main_item:
            for sub_item1 in main_item['items']:
                sub_item = sub_item1['item']
                if sub_item.get('is_separator', False):
                    main_menu.addSeparator()
                    continue

                title  = sub_item['title']
                action = QtWidgets.QAction(title, main_window)
                action.triggered.connect(functools.partial(exec_action, provider,
                                                           function_name=sub_item.get('action', None)))
                # action = QTAux.MenuItem('1', sub_item['title'], self.provider, sub_item.get('action', None),
                #                        None, self)
                main_menu.addAction(action)
    return menu_bar


def create_toolbar(config, main_window, provider, key='toolbar', icon_key='icon', tooltip_key='tooltip',
                   combo_key='Combo', check_key='Check', type_key='type', label_key='Label', action_key='Action'):
    widgets = []
    if key not in config:
        return None, widgets

    toolbar        = QtWidgets.QToolBar()
    toolbar_config = config[key]
    for i, item1 in enumerate(toolbar_config):
        item      = item1['item']
        title     = item.get('title', '')
        name      = item.get('name', 'Item_%s' % i)
        item_type = item.get(type_key, 'Action')
        tooltip   = item.get(tooltip_key, None)

        if item.get('is_separator', False):
            toolbar.addSeparator()
        elif item_type == combo_key:
            widgets.append(QTAux.Combo(name, title, provider, None, toolbar, item))
        elif item_type == check_key:
            widgets.append(QTAux.CheckButton(name, title, provider, None, toolbar, tooltip))
        elif item_type == label_key:
            QTAux.Label(name, title, provider, None, toolbar, align_left=False)
        elif item_type == action_key:
            provider.set_value(name, title)
            action = QTAux.Action(name, title, provider, main_window, item, tooltip=tooltip)
            action.qt_action.triggered.connect(functools.partial(exec_action, provider,
                                                                 function_name=item.get('action', None)))
            toolbar.addAction(action.qt_action)
            widgets.append(action)
        else:
            raise Exception('%s is not implemented in Toolbar' % item_type)

    return toolbar, widgets


def create_status_bar(win_config, main_window, status_key='status_bar'):
    if not win_config.get(status_key, True):  # create a statusbar unless is explicitly forbidden
        return None
    statusbar = QtWidgets.QStatusBar(main_window)
    main_window.setStatusBar(statusbar)
    return statusbar


class GeneralProgressBar:
    """
    Handle a ProgressBar to be used inside any widget, main use is to put it in a StatusBar
    Note: if widget is None all methods must work anyway, in order to free all calling usage to check whether
          ProgressBar is present or not
    """

    def __init__(self, widget=None, stretch=0, visible=False):
        """
        init
        :param widget:  widget where the progress bar will show. due to some initialization timing sometime widget can
                        be None
        :param stretch: amount of extra space to be used inside widget. 0 means original size, usually 1 is enough to
                        guarantee it will occupy the full widget
        :param visible:
        """
        self.parent = widget
        if self.parent is None:
            return
        self.progress_bar = QtWidgets.QProgressBar(parent=self.parent)
        self.parent.addWidget(self.progress_bar, stretch=stretch)
        self.progress_bar.setVisible(visible)

    def get_maximum(self):
        if self.parent is None:
            return
        return self.progress_bar.maximum()

    def get_value(self):
        if self.parent is None:
            return
        return self.progress_bar.value()

    def reset(self, text=None):
        if self.parent is None:
            return
        self.progress_bar.reset()
        self.progress_bar.setVisible(False)
        if text is not None and self.parent is not None:
            self.parent.showMessage(text)

    def set_max(self, max_value):
        if self.parent is None:
            return
        self.progress_bar.setMaximum(max_value)
        self.progress_bar.setVisible(True)

    def set_value(self, value):
        if self.parent is None:
            return
        self.progress_bar.setValue(value)

    def add_increment(self, increment):
        if self.parent is None:
            return
        self.progress_bar.setValue(self.progress_bar.value()+increment)


# Widgets definition
def add_widgets_to_window(layout, layout_config, window):
    widgets = layout_config.get('widgets', [])
    return def_widgets(widgets, window.provider, layout)


def def_widgets(widgets_definition, provider, layout):
    widgets = [def_widget(widget, provider, layout) for widget in widgets_definition]
    return widgets


def def_widget(widget1, provider, layout, main_key='widget'):
    widget  = widget1[main_key]
    c_name  = widget['name']
    e_name  = external_name(widget)
    c_type  = widget['type']
    tooltip = widget.get('tooltip', None)
    action  = action_string(widget)
    value   = get_widget_initial_value(c_name, widget, provider)
    # print('%s initial value: %s' % (c_name, value))
    if value is not None:
        # value must be set before widget creation, so it will appear the first time the widget is displayed
        provider.set_value(c_name, value)

    if c_type == 'Slider':
        qt_widget = def_slider(c_name, e_name, provider, layout, widget['parms'], action, tooltip=tooltip)
    elif c_type == 'Combo':
        qt_widget = QTAux.Combo(c_name, e_name, provider, action, layout, widget, tooltip=tooltip)
    elif c_type == 'EnumCombo':
        enum       = eval(widget['enum'])
        qt_widget = QTAux.EnumCombo(c_name, e_name, provider, enum, action, layout)
        # qt_widget = def_enum_combo(c_name, e_name, provider, layout, action, widget)
    elif c_type == 'Button':
        qt_widget = def_button(c_name, e_name, provider, layout, action, widget, tooltip=tooltip)
    elif c_type == 'Constant':
        qt_widget = def_constant(c_name, e_name, provider, layout, action)
    elif c_type == 'Check':
        qt_widget = QTAux.CheckButton(c_name, e_name, provider, action, layout, tooltip=tooltip)
    elif c_type in ['Text', 'Label']:
        qt_widget = QTAux.Label(c_name, e_name, provider, action, layout)
    elif c_type == 'EditText':
        qt_widget = QTAux.EditText(c_name, e_name, provider, action, layout, tooltip=tooltip)
    elif c_type == 'EditNumber':
        qt_widget = QTAux.EditNumber(c_name, e_name, provider, action, layout)
    elif c_type == 'EditNumberSpin':
        qt_widget = QTAux.EditNumberSpin(c_name, e_name, provider, action, layout, widget)
    elif c_type == 'ProgressBar':
        qt_widget = QTAux.ProgressBar(c_name, provider, action, layout)
    else:
        raise Exception('Widget type "%s" not implemented' % c_type)

    qt_widget.refresh_others = widget.get('refresh_others', False)

    return qt_widget


def get_widget_initial_value(c_name, widget, provider, key_value='value'):
    if key_value in widget:
        return widget[key_value]
    elif provider.widget_has_value(c_name):
        return provider.get_value(c_name)
    else:
        return None


def def_slider(c_name, e_name, provider, layout, parms, action, tooltip=None):
    [min_e, max_e, scale_e] = parms
    min1   = get_def_value(min_e, provider)
    max1   = get_def_value(max_e, provider)
    scale1 = get_def_value(scale_e, provider)
    return QTAux.Slider(c_name, e_name, provider, min1, max1, action, layout, tooltip=tooltip, scale=scale1)


def def_button(c_name, e_name, provider, layout, action, widget, tooltip=None, def_width=30, def_length=100):
    if action != '':
        width  = widget.get('width', def_width)
        length = widget.get('length', def_length)
        return QTAux.Button(c_name, e_name, provider, action, layout, tooltip=tooltip, width=width, length=length)
    else:
        raise Exception('Invalid button definition, no action defined')


def def_constant(c_name, e_name, provider, layout, action):
    # Only reason to have a constant on window is to exec an action
    if action != '':
        QTAux.Constant(c_name, e_name, provider, action, layout)
    else:
        raise Exception('Invalid constant definition, no action defined')


def external_name(item, title_key='title', desc_key='desc', name_key='name'):
    if title_key in item:
        k = title_key
    elif desc_key in item:
        k = desc_key
    else:
        k = name_key
    return item[k]


def get_with_default(values, key, default):
    if key in values:
        return values[key]
    else:
        return default


def get_def_value(v, provider):
    # Note: provider is necessary so eval can use it
    string = QTAux.string_to_eval(v)
    return eval(string) if string is not None else v


def action_string(widget_def, action_key='action'):
    return widget_def.get(action_key, '')


def exec_action(provider, function_name=None):
    # Note: provider is necessary so eval can use it
    if function_name is None:
        return
    full_function_name = 'provider.%s()' % function_name
    eval(full_function_name)


# Visualizations
def show_text_values(ax, values, x, y, boxstyle='round', facecolor='wheat', alpha=0.5, vertical_alignment='top'):
    """
    Display a list of values (name=value) in a text box
    :param ax:
    :param values: :type list of [nane, value]
    :param x:
    :param y:
    :param boxstyle:
    :param facecolor:
    :param alpha:
    :param vertical_alignment:
    :return:
    """
    if not values:
        return
    text_string = ''
    next1       = ''
    for [name, value] in values:
        text_string += r'%s$%s=%s$' % (next1, name, value)
        next1 = '\n'
    props = dict(boxstyle=boxstyle, facecolor=facecolor, alpha=alpha)
    ax.text(x, y, text_string, verticalalignment=vertical_alignment, bbox=props)


def get_arg_value(i, default):
    return default if len(sys.argv) < i + 1 else sys.argv[i]
