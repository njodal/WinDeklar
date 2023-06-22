import random
import math
import matplotlib.lines as mlines

import points_box as pb


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


def graph_points(ax, points, inc=1.1, scale_type='scaled', x_visible=True, y_visible=True, line_width=1.0, color='Blue'):
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
            line     = mlines.Line2D([first_point[0], x2], [first_point[1], y2], color=color, linewidth=line_width)
            ax.add_line(line)
            first_point = [x2, y2]
    point_box.set_bounds(ax, inc)


def random_function(from_x, to_x, min_y=0, max_y=10):
    return [[x, random.randint(min_y, max_y)] for x in range(from_x, to_x)]


def get_function_xy_values(function, from_x, to_x, inc=math.radians(5)):
    points = []
    x      = 0.0
    for i in range(from_x, to_x):
        points.append([x, function(x)])
        x += inc
    return points


