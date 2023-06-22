#!/usr/bin/env python

import sys
import math
import random
import time
import matplotlib.lines as mlines

import QTAux
import WindowForm as WinForm
import points_box as pb
import record as rc
import yaml_functions


class ExampleHost(WinForm.HostModel):
    """
    Shows tentacles
    """

    def __init__(self, default_directory='/tmp', file_extension='yaml'):
        # keys (names used in the yaml definition file)
        self.check1_key = 'check1'
        self.points_key = 'points'
        self.axis_key   = 'show_axis'
        self.type_key   = 'graph_type'
        self.action_key = 'action'
        self.width_key  = 'line_width'

        # particular data
        self.action_name        = 'Action'
        self.last_action_number = 0
        self.directory          = default_directory
        self.file_extension     = file_extension
        self.file_filter        = '*.%s' % self.file_extension
        self.file_name          = None

        initial_values = {}
        super(ExampleHost, self).__init__(initial_values=initial_values)

    def update_view(self, ax):
        """
        Update the figure
        Notes:
            - This method is called when any property changes or refresh() is used
            - All form variables are in dict self.state
        :param ax:
        :return:
        """
        points = self.get_graph_points()
        show_axis = [True, True] if self.state.get(self.axis_key, True) else [False, False]
        graph_points(ax, points, x_visible=show_axis[0], y_visible=show_axis[1],
                     line_width=self.state.get(self.width_key, 1.0))

    def redraw(self):
        """
        Event defined in the yaml file to be called when button redraw is pressed
        :return:
        """
        self.refresh()

    # actions
    def event_open_file(self):
        """
        Event defined in the yaml file to be called when File/Open is clicked
        :return:
        """
        file_name = self.get_file_name(title='Open an YAML', file_filter=self.file_filter, directory=self.directory)
        if file_name is None:
            return
        self.file_name = file_name
        # particular code to open the file
        self.open_yaml_file(self.file_name,progress_bar=self.get_progress_bar())

    def event_save_file_as(self):
        file_name = self.get_file_name_to_save(title='Save File', file_filter=self.file_filter, directory=self.directory)
        if file_name is None:
            return
        self.save_file(file_name, progress_bar=self.get_progress_bar())

    def event_save_file(self):
        if self.file_name is None:
            self.event_save_file_as()
        else:
            self.save_file(self.file_name, progress_bar=self.get_progress_bar())

    def change_action(self):
        self.last_action_number += 1
        value = '%s %s' % (self.action_name, self.last_action_number)
        self.set_and_refresh_control(self.action_key, value)

    # particular code
    def open_yaml_file(self, file_name, progress_bar):
        """
        Example on how to use the progress bar
        :param file_name:
        :param progress_bar: use to give feedback about the opening process
        :return:
        """
        file = yaml_functions.get_yaml_file(file_name, must_exist=True, verbose=True)
        self.state.update(file['state'])
        print(self.state)
        self.refresh()

        # just an example of how to use the ProgressBar, no actually needed in this case
        progress_bar_example(progress_bar, max_value=100, inc=20, sleep_time=0.2)

        msg = '%s opened' % file_name
        self.show_status_bar_msg(msg)

    def save_file(self, file_name, progress_bar):
        """
        Example on how to use the progress bar
        :param file_name:
        :param progress_bar: use to give feedback about the opening process
        :return:
        """
        record = rc.Record(file_name, dir=None, add_time_stamp=False)
        record.write_ln('version: 1')  # just to avoid warnings with editing in pycharm
        record.write_group('state', self.state, level=0)

        # just an example of how to use the ProgressBar, no actually needed in this case
        progress_bar_example(progress_bar, max_value=100, inc=20, sleep_time=0.2)

        msg = '%s saved' % file_name
        self.show_status_bar_msg(msg)

    def get_graph_points(self):
        """
        Returns the points (x,y) to be graphed depending on the graph type and number of points
        :return:
        """
        graph_type = self.state.get(self.type_key, 'None')
        number_of_points = int(self.state.get(self.points_key, 10))
        if graph_type == 'Random':
            points = random_function(0, number_of_points)
        elif graph_type == 'Sine':
            points = any_function(0, number_of_points, math.sin, inc=math.radians(10))
        elif graph_type == 'Cosine':
            points = any_function(0, number_of_points, math.cos, inc=math.radians(10))
        else:
            self.show_status_bar_msg('%s not implemented' % graph_type)
            points = []
        return points


def progress_bar_example(progress_bar, max_value=100, inc=20, sleep_time=0.2):
    progress_bar.set_max(max_value)
    for i in range(0, max_value, inc):
        progress_bar.set_value(i)
        time.sleep(sleep_time)


def graph_points(ax, points, inc=1.1, scale_type='scaled', x_visible=True, y_visible=True, line_width=1.0):
    point_box = pb.PointsBox()
    point_box.add_points(points)  # to calc bounds
    ax.axis(scale_type)
    ax.get_xaxis().set_visible(x_visible)
    ax.get_yaxis().set_visible(y_visible)
    number_of_points = len(points)
    if number_of_points == 0:
        pass
    else:
        first_point = points[0]
        for i in range(1, number_of_points):
            [x2, y2] = points[i]
            line     = mlines.Line2D([first_point[0], x2], [first_point[1], y2], linewidth=line_width)
            ax.add_line(line)
            first_point = [x2, y2]
    point_box.set_bounds(ax, inc)


def random_function(from_x, to_x, min_y=0, max_y=10):
    return [[x, random.randint(min_y, max_y)] for x in range(from_x, to_x)]


def any_function(from_x, to_x, function, inc=math.radians(5)):
    points = []
    x      = 0.0
    for i in range(from_x, to_x):
        points.append([x, function(x)])
        x += inc
    return points


if __name__ == '__main__':
    app = QTAux.def_app()
    win_config_name = 'view_example.yaml'

    provider = ExampleHost()
    myGUI = WinForm.ConfigurableWindow(win_config_name, provider)
    sys.exit(app.exec_())
