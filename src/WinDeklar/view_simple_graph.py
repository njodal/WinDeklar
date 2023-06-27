from WinDeklar.WindowForm import SimpleFigure
import WinDeklar.graph_aux as ga


def show_simple_window(title='Sine and Cosine graph', number_of_points=100, size=(5, 2),
                       functions=(('Sine', 'Blue'), ('Cosine', 'Red'))):
    window = SimpleFigure(title=title, size=size, adjust_size=False)
    for [function_name, color] in functions:
        graph_one_function(function_name, window.ax, number_of_points, color)
    window.show()


def graph_one_function(function_name, ax, number_of_points, color):
    points, msg = ga.graph_points_for_many_functions(function_name, number_of_points)
    if points is None:
        print('%s not implemented' % function_name)
        return
    ga.graph_points(ax, points, color=color)


if __name__ == '__main__':
    show_simple_window()
