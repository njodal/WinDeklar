import numpy as np
import random
import math
import matplotlib.lines as mlines


class RealTimeDataProvider(object):
    def __init__(self, dt=0.1, min_y=0.0, max_y=10.0, color='Red'):
        self.min_y = min_y
        self.max_y = max_y
        self.color = color
        self.dt    = dt
        self.t     = 0.0

    def get_bounds(self):
        return self.min_y, self.max_y

    def get_min_y(self):
        return self.min_y

    def get_max_y(self):
        return self.max_y

    def get_next_values(self, i):
        x      = self.t
        self.t += self.dt
        y      = i
        return x, y


class RealTimeRandomDataProvider(RealTimeDataProvider):
    """
    Returns a random number between min_y and max_y
    """
    def __init__(self, dt=0.1, min_y=0.0, max_y=10.0, color='Red'):
        super(RealTimeRandomDataProvider, self).__init__(dt=dt, min_y=min_y, max_y=max_y, color=color)

    def get_next_values(self, i):
        x      = self.t
        self.t += self.dt
        return x, np.random.uniform(self.min_y, self.max_y)


class RealTimeFunctionDataProvider(RealTimeDataProvider):
    """
    Returns the result of applying a given function (function)
    """

    def __init__(self, dt=0.1, min_y=-1.2, max_y=1.2, function=np.sin, inc=np.radians(10), color='Red'):
        self.function = function
        self.inc      = inc
        self.last_r   = 0.0
        super(RealTimeFunctionDataProvider, self).__init__(dt=dt, min_y=min_y, max_y=max_y, color=color)

    def get_next_values(self, i):
        x      = self.t
        self.t += self.dt
        y = self.function(self.last_r)
        self.last_r += self.inc
        return x, y


class RealTimeConstantDataProvider(RealTimeDataProvider):
    def __init__(self, dt=0.1, min_y=0.0, max_y=10.0, color='Black'):
        self.reference = 0.0
        super(RealTimeConstantDataProvider, self).__init__(dt=dt, min_y=min_y, max_y=max_y, color=color)

    def set_reference(self, new_reference):
        self.reference = new_reference

    def get_next_values(self, i):
        x      = self.t
        self.t += self.dt
        return x, self.reference


def graph_points_for_many_functions(function_name, number_of_points):
    msg = ''
    if function_name == 'Random':
        points = random_function(0, number_of_points)
    elif function_name == 'Sine':
        points = get_function_xy_values(math.sin, 0, number_of_points, inc=math.radians(10))
    elif function_name == 'Cosine':
        points = get_function_xy_values(math.cos, 0, number_of_points, inc=math.radians(10))
    else:
        points = None
        msg    = '%s not implemented' % function_name
    return points, msg


def graph_points(ax, points, scale_type='scaled', x_visible=True, y_visible=True, line_width=1.0, color='Blue'):
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
            line     = mlines.Line2D([first_point[0], x2], [first_point[1], y2], color=color, linewidth=line_width)
            ax.add_line(line)
            first_point = [x2, y2]


def random_function(from_x, to_x, min_y=0, max_y=10):
    # x = np.linspace(from_x, to_x)
    # y = np.random.randint(min_y, max_y, len(x))
    # return x, y
    return [[x, random.randint(min_y, max_y)] for x in range(from_x, to_x)]


def get_function_xy_values(function, from_x, to_x, inc=math.radians(5)):
    points = []
    x      = 0.0
    for i in range(from_x, to_x):
        points.append([x, function(x)])
        x += inc
    return points
