#!/usr/bin/env python

import sys
import time

import WinDeklar.WindowForm as WinForm
import WinDeklar.graph_aux as ga
import WinDeklar.QTAux as QTAux
import WinDeklar.record as rc
import WinDeklar.yaml_functions as ya


class ExampleHost(WinForm.HostModel):
    """
    Example of a Form with many features:
        * Open and Save files
        * Toolbar
        * Many kinds of controls (Slider, Combo, Check, Button, etc.)
        * Mouse move
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

        initial_values = {}  # used in case some control have an initial value programmatically
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
        ga.graph_points(ax, points, x_visible=show_axis[0], y_visible=show_axis[1],
                        line_width=self.state.get(self.width_key, 1.0))
        self.resize_figure(ax, points)

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
        self.open_yaml_file(self.file_name, progress_bar=self.get_progress_bar())

    def event_save_file_as(self):
        file_name = self.get_file_name_to_save(title='Save File', file_filter=self.file_filter,
                                               directory=self.directory)
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

    def on_mouse_move(self, event, ax):
        if event.xdata is None or event.ydata is None:
            return
        self.show_status_bar_msg('x:%.2f y:%.2f' % (event.xdata, event.ydata))

    # particular code
    def open_yaml_file(self, file_name, progress_bar):
        """
        Example on how to use the progress bar
        :param file_name:
        :param progress_bar: use to give feedback about the opening process
        :return:
        """
        file = ya.get_yaml_file(file_name, must_exist=True, verbose=True)
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
        function_name    = self.state.get(self.type_key, 'None')
        number_of_points = int(self.state.get(self.points_key, 10))
        points, msg      = ga.graph_points_for_many_functions(function_name, number_of_points)
        if points is None:
            self.show_status_bar_msg('%s not implemented' % function_name)
            points = []
        return points


def progress_bar_example(progress_bar, max_value=100, inc=20, sleep_time=0.2):
    progress_bar.set_max(max_value)
    for i in range(0, max_value, inc):
        progress_bar.set_value(i)
        time.sleep(sleep_time)


if __name__ == '__main__':
    app = QTAux.def_app()
    provider = ExampleHost()        # class to handle events
    WinForm.set_winform(__file__, provider)
    sys.exit(app.exec_())
