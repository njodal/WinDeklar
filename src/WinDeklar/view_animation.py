#!/usr/bin/env python

import sys
import numpy as np

import WinDeklar.QTAux as QTAux
import WinDeklar.WindowForm as WinForm
import WinDeklar.graph_aux as ga


class ExampleHost(WinForm.HostModel):
    """
    Shows two animated graphs
    """

    def __init__(self, function1=np.sin, function2=np.cos, color='Blue', y_bounds=(-1.2, 1.2)):
        # keys (names used in the yaml definition file)
        self.start_stop_key        = 'start_stop'
        self.start_stop_action_key = 'start_stop_action'
        self.graph1_key = 'graph1'
        self.graph2_key = 'graph2'

        # particular data
        self.function1 = function1
        self.function2 = function2
        self.color    = color
        self.y_bounds = y_bounds

        initial_values = {}
        super(ExampleHost, self).__init__(initial_values=initial_values)

    def get_data_provider(self, figure, interval=100, min_x=0.0, max_x=10.0, data_provider=None):
        """
        Returns the basic setup of the graph, most important one is the data provider
        :param figure:
        :param interval:       time in milliseconds to show each point in the graph
        :param min_x:          start value in the x-axis
        :param max_x:          max value in the x-axis, after that it starts to scroll left
        :param data_provider:  subclass of RealTimeDataProvider
        :return:
        """
        if figure.name == self.graph1_key:
            function = self.function1
        elif figure.name == self.graph2_key:
            function = self.function2
        else:
            raise Exception('"%s" graph name not implemented (valids are %s and %s)' %
                            (figure.name, self.graph1_key, self.graph2_key))

        dt             = interval/1000  # seconds
        max_points     = int(max_x/dt) + 1
        x_bounds       = [min_x, max_x]
        data_provider1 = [ga.RealTimeFunctionDataProvider(dt=dt, min_y=self.y_bounds[0], max_y=self.y_bounds[1],
                                                          function=function, color=self.color)]
        return interval, max_points, x_bounds, data_provider1

    def start_stop(self):
        """
        Logit to start/stop the graph with only one button (who changes its title depending on the graph is
        running or not_
        :return:
        """
        is_running = self.start_stop_animation()
        if is_running:
            self.set_widget_title(self.start_stop_key, 'Pause Animation')
            self.set_widget_title(self.start_stop_action_key, 'Pause Animation')
        else:
            self.set_widget_title(self.start_stop_key, 'Restart Animation')
            self.set_widget_title(self.start_stop_action_key, 'Restart Animation')


if __name__ == '__main__':
    app = QTAux.def_app()
    provider = ExampleHost()        # class to handle the WinForm logic
    WinForm.run_winform(__file__, provider)
    sys.exit(app.exec_())
