#!/usr/bin/env python

import sys
import time

import WindowForm as WinForm
import WinDeklar.QTAux as QTAux
import WinDeklar.yaml_functions as yf


class ExampleHost(WinForm.HostModel):
    """
    Example of editable drawing
    """

    def __init__(self, file_name, default_directory='/tmp', file_extension='yaml'):
        # keys (names used in the yaml definition file)
        self.view_lines_key = 'view_lines'
        self.action_key = 'action'
        self.width_key  = 'line_width'
        self.graph1_key = 'graph1'

        # particular data
        self.figure    = None
        self.metadata_file_name = None

        self.action_name        = 'Action'
        self.last_action_number = 0
        self.directory          = default_directory
        self.file_extension     = file_extension
        self.file_filter        = '*.%s' % self.file_extension
        self.file_name          = file_name

        initial_values = {}  # used in case some control needs to have an initial value programmatically
        super(ExampleHost, self).__init__(initial_values=initial_values)

    def widget_changed(self, name, value):
        """
        Called when a control has changed it values
        :param name:
        :param value:
        :return:
        """
        if name == self.view_lines_key:
            if self.figure is None:
                return
            self.figure.set_visible_type('line', value)

    def update_view(self, figure, ax):
        """
        Update the figure
        Notes:
            - This method is called when any property changes or refresh() is used
            - All form variables are accessible by get_value
        :param figure:
        :param ax:
        :return:
        """
        if figure.name != self.graph1_key or self.figure is not None:
            return

        # just load items the first time the figure appears
        self.figure = figure  # assure not call again initialization
        if self.file_name is not None:
            items_def = yf.get_yaml_file(self.file_name, directory=None)
            self.figure.load_drawing(items_def)

    def redraw(self):
        """
        Event defined in the yaml file to be called when button redraw is pressed
        :return:
        """
        self.refresh()

    # actions
    def undo(self):
        if self.figure is None:
            return
        self.figure.undo()

    def redo(self):
        if self.figure is None:
            return
        self.figure.redo()

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
        self.set_and_refresh_widget(self.action_key, value)

    def on_mouse_move(self, event, ax):
        if event.xdata is None or event.ydata is None:
            return
        self.show_status_bar_msg('x:%.2f y:%.2f' % (event.xdata, event.ydata))

    def delete_selected_items(self):
        if self.figure is None:
            return
        print(self.figure.get_items())
        # self.figure.delete_selected_items()
        # print('Delete selected items')

    def clear(self):
        if self.figure is None:
            return
        self.figure.clear()

    # particular code
    def open_yaml_file(self, file_name, progress_bar):
        """
        Example on how to use the progress bar
        :param file_name:
        :param progress_bar: use to give feedback about the opening process
        :return:
        """
        file = yf.get_yaml_file(file_name, must_exist=True, verbose=True)
        self.load_drawing(file)
        self.refresh()

        msg = '%s opened' % file_name
        self.show_status_bar_msg(msg)

    def save_file(self, file_name, progress_bar):
        """
        Example on how to use the progress bar
        :param file_name:
        :param progress_bar: use to give feedback about the opening process
        :return:
        """
        if self.figure is None:
            return

        to_save = self.figure.get_drawing()
        yf.save_yaml_file(to_save, file_name, directory=None)
        msg = '%s saved' % file_name
        self.show_status_bar_msg(msg)

    def load_drawing(self, drawing_def, items_key='items'):
        if items_key not in drawing_def:
            self.show_status_bar_msg('Invalid format')
            return
        self.figure.clear()
        fail_msgs = self.figure.add_items(drawing_def)
        for fail_msg in fail_msgs:
            print(fail_msg)


def progress_bar_example(progress_bar, max_value=100, inc=20, sleep_time=0.2):
    progress_bar.set_max(max_value)
    for i in range(0, max_value, inc):
        progress_bar.set_value(i)
        time.sleep(sleep_time)


if __name__ == '__main__':
    app = QTAux.def_app()
    drawing_name = WinForm.get_arg_value(1, None)

    provider = ExampleHost(drawing_name)        # class to handle form specific logic
    WinForm.run_winform(__file__, provider)
    sys.exit(app.exec_())
