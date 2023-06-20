#!/usr/bin/env python

import sys
import math
import random
import time
import matplotlib.lines as mlines

import QTAux
import WindowForm as WinForm
import points_box as pb


class ExampleHost(WinForm.HostModel):
    """
    Shows tentacles
    """

    def __init__(self):
        # keys
        self.check1_key = 'check1'
        self.points_key = 'points'
        self.axis_key   = 'show_axis'
        self.type_key   = 'graph_type'
        self.action_key = 'action'
        self.width_key  = 'line_width'

        self.action_name        = 'Action'
        self.last_action_number = 0

        initial_values = {}
        super(ExampleHost, self).__init__(initial_values=initial_values)

    def update_view(self, ax):
        """
        Updates the figure
        :param ax:
        :return:
        """
        points = self.get_graph_points()
        show_axis = [True, True] if self.state.get(self.axis_key, True) else [False, False]
        graph_points(ax, points, x_visible=show_axis[0], y_visible=show_axis[1],
                     line_width=self.state.get(self.width_key, 1.0))

    def redraw(self):
        self.refresh()

    # actions
    def open_a_file(self):
        self.open_file(self.open_yaml_file, title='Open an YAML', file_filter='*.yaml', directory='', done_msg=None)

    def open_yaml_file(self, file_name, progress_bar=None):
        if progress_bar is not None:
            # example on how to use the progress bar
            max_i = 100
            progress_bar.set_max(max_i)
            for i in range(0, max_i, 20):
                progress_bar.set_value(i)
                time.sleep(0.2)

        msg = '%s opened' % file_name
        self.show_status_bar_msg(msg)

    def change_action(self):
        self.last_action_number += 1
        value = '%s %s' % (self.action_name, self.last_action_number)
        self.set_and_refresh_control(self.action_key, value)

    def get_graph_points(self):
        graph_type       = self.state.get(self.type_key, 'None')
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
