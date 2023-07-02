#!/usr/bin/env python

import sys
import numpy as np

import WinDeklar.QTAux as QTAux
import WinDeklar.WindowForm as WinForm
import WinDeklar.graph_aux as ga


class ExampleHost(WinForm.HostModel):
    """
    Shows tentacles
    """

    def __init__(self, function=np.sin, color='Blue', y_bounds=(-1.2, 1.2)):
        # keys (names used in the yaml definition file)
        self.start_stop_key        = 'start_stop'
        self.start_stop_action_key = 'start_stop_action'

        # particular data
        self.function = function
        self.color    = color
        self.y_bounds = y_bounds

        initial_values = {}
        super(ExampleHost, self).__init__(initial_values=initial_values)

    def get_data_provider(self, interval=100, min_x=0.0, max_x=10.0, data_provider=None):
        """
        Returns the basic setup of the graph, most important one is the data provider
        :param interval:       time in milliseconds to show each point in the graph
        :param min_x:          start value in the x-axis
        :param max_x:          max value in the x-axis, after that it starts to scroll left
        :param data_provider:  subclass of RealTimeDataProvider
        :return:
        """
        dt             = interval/1000  # seconds
        max_points     = int(max_x/dt) + 1
        x_bounds       = [min_x, max_x]
        data_provider1 = [ga.RealTimeFunctionDataProvider(dt=dt, min_y=self.y_bounds[0], max_y=self.y_bounds[1],
                                                          function=self.function, color=self.color)]
        return interval, max_points, x_bounds, data_provider1

    def start_stop_animation(self):
        """
        Logit to start/stop the graph with only one button (who changes its title depending on the graph is
        running or not_
        :return:
        """
        if self.anim_is_running():
            self.stop_animation()
            self.set_control_title(self.start_stop_key, 'Restart Animation')
            self.set_control_title(self.start_stop_action_key, 'Restart Animation')
        else:
            self.start_animation()
            self.set_control_title(self.start_stop_key, 'Pause Animation')
            self.set_control_title(self.start_stop_action_key, 'Pause Animation')


if __name__ == '__main__':
    app = QTAux.def_app()
    provider = ExampleHost()        # class to handle the WinForm logic
    WinForm.run_winform(__file__, provider)
    sys.exit(app.exec_())
