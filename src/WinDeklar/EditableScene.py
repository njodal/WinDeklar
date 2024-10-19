import math
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QUndoStack, \
    QGraphicsItem, QGraphicsLineItem, QGraphicsPolygonItem
from PyQt5.QtCore import QRectF, Qt, QPointF, QLineF
from PyQt5.QtGui import QPen, QColor, QPolygonF


class EditableFigure(QGraphicsView):
    name_key = 'name'

    def __init__(self, parent, config, multiple_selection=True, scale_factor=100):
        """
        A figure that have items inside that can be editables (move, change size, etc)
        :param parent: main window
        :param config: config options :type Dict
        :param multiple_selection: whether allow selecting many options at once
        :param scale_factor: factor to relate pixels to meters
        """
        super().__init__()
        self.name   = config.get(self.name_key, 'no_name')
        self.parent = parent
        self.scene  = QGraphicsScene(self)
        self.setScene(self.scene)
        self.undo_stack = QUndoStack()
        if multiple_selection:
            self.setDragMode(QGraphicsView.RubberBandDrag)

        self.scale_factor = scale_factor
        self.scale(1, -1)  # to point y-axis forward, not backward

        # zoom parameters
        self.zoom_factor  = 1.15
        self.min_zoom     = 0.1
        self.max_zoom     = 10.0
        self.current_zoom = 1.0

    def add_item(self, item):
        self.scene.addItem(item)

    def delete_item(self, item):
        self.scene.removeItem(item)

    def delete_selected_items(self):
        for item in self.scene.selectedItems():
            self.delete_item(item)

    def clear(self):
        # ToDo: not working
        self.items().clear()
        self.scene.update()
        print('clear')

    def selected_items(self):
        for item in self.view.scene.selectedItems():
            yield item

    # events
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            print("Clic derecho detectado")
        # elif event.button() == Qt.LeftButton:
        #    print("Clic izquierdo detectado")
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        """
        Capture mouse wheel to zoom in or out
        :param event:
        :return:
        """
        if event.angleDelta().y() > 0:
            # Zoom in
            self.zoom_in()
        else:
            # Zoom out
            self.zoom_out()

    def zoom_in(self):
        if self.current_zoom * self.zoom_factor < self.max_zoom:
            self.scale(self.zoom_factor, self.zoom_factor)
            self.current_zoom *= self.zoom_factor

    def zoom_out(self):
        if self.current_zoom / self.zoom_factor > self.min_zoom:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
            self.current_zoom /= self.zoom_factor

    def update_figure(self):
        """
        Initialize the scene with items from provider
        :return:
        """
        # print('update figure')
        self.items().clear()
        self.parent.provider.update_view(self, None)  # calls provider to get the initial items
        # self.parent.provider.apply_zoom()
        # self.draw()


class SceneItems(object):
    """
    Keeps the items present in a scene
    """

    def __init__(self):
        self.index = 0
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def delete_item(self, item):
        self.items.remove(item)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.items):
            item = self.items[self.index]
            self.index += 1
            return item
        else:
            raise StopIteration


class SceneItem(QGraphicsItem):
    """
    Base class for any item in a scene, provides all the common functionality

    """
    is_movable_key    = 'is_movable'
    is_selectable_key = 'is_selectable'

    def __init__(self, item_def):
        """
        Super class to define an item that can be
        :param item_def:
        """
        super().__init__()
        if item_def.get(self.is_movable_key, False):
            self.setFlag(QGraphicsItem.ItemIsMovable)
        if item_def.get(self.is_selectable_key, False):
            self.setFlag(QGraphicsItem.ItemIsSelectable)


class SceneLine(QGraphicsLineItem):
    """
    A movable, resizable line
    """
    def __init__(self, start_point, end_point, name='', scale_factor=100.0):
        """
        Define a line
        :param start_point: in meters
        :param end_point:   in meters
        :param scale_factor: scale factor to convert to pixels
        """
        self.handles       = []
        self.scale_factor  = scale_factor
        self.name          = ''
        start_point_pixels = point_to_pixel_point(start_point, self.scale_factor)
        end_point_pixels   = point_to_pixel_point(end_point, self.scale_factor)
        line               = QLineF(start_point_pixels, end_point_pixels)
        super().__init__(line)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        # self.setFlag(QGraphicsItem.ItemIsSelectable)

        if self.name != '':
            # ToDo: not working, tooltip doesn't appear
            self.setToolTip(self.name)

        self.is_resizing  = False
        handle_start      = EnlargeHandle(self, True, self.scale_factor)     # enlarge start point
        handle_end        = EnlargeHandle(self, False, self.scale_factor)    # enlarge end point
        handle_start_move = RotateHandle(self, True, self.scale_factor)      # rotate around end point
        handle_end_move   = RotateHandle(self, False, self.scale_factor)     # rotate around start point
        self.handles = [handle_start, handle_end, handle_start_move, handle_end_move]

    def p1(self):
        return self.line().p1()

    def p2(self):
        return self.line().p2()

    def start_point(self):
        return pixel_point_to_point(self.p1(), self.scale_factor, self.pos())

    def end_point(self):
        return pixel_point_to_point(self.p2(), self.scale_factor, self.pos())

    def length_in_pixels(self):
        """
        Returns the line length in pixels
        :return:
        """
        return distance_in_pixels(self.p1(), self.p2())

    def update_line_end_point(self, is_start, new_pos):
        """
        Update one of the line end points depending on the is_start flag
        :param is_start: if True update start end point, else the other one
        :param new_pos:
        :return:
        """
        p1, p2 = [new_pos, self.p2()] if is_start else [self.p1(), new_pos]
        self.setLine(QLineF(p1, p2))

    # handles
    def stick_to_line_handles(self):
        for handle in self.handles:
            handle.move_to_line()

    def set_visible_handles(self, is_visible, non_check_handle=None):
        """
        Turn on of off all handles
        :param is_visible:
        :param non_check_handle: do not apply to this handle, useful to let this one visible when it's active
        :return:
        """
        for handle in self.handles:
            if handle == non_check_handle:
                continue
            handle.setVisible(is_visible)

    # events
    def mousePressEvent(self, event):
        """
        Allow all handles
        :param event:
        :return:
        """
        self.set_visible_handles(True)
        super().mousePressEvent(event)

    def __str__(self):
        return 'line %s,%s' % (self.start_point(), self.end_point())


class EnlargeHandle(QGraphicsPolygonItem):
    """
    Handle to enlarge one end of a line
    """
    def __init__(self, parent_line, is_start, scale_factor, size=10, t=0.9, color=(255, 255, 255)):
        self.size         = size
        self.t            = t
        self.is_start     = is_start
        self.parent_line  = parent_line
        self.scale_factor = scale_factor

        super().__init__()
        self.setBrush(QColor(color[0], color[1], color[2]))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)  # to send itemChange
        self.setParentItem(parent_line)

        self.move_to_line()

        self.setVisible(False)

    def move_to_line(self):
        pp1, pp2 = self.ordered_end_points()
        polygon  = get_arrow_head(pp1, pp2, self.size, percentage=self.t)
        self.setPolygon(polygon)

    def selected_end_point(self):
        return self.parent_line.p1() if self.is_start else self.parent_line.p2()

    def ordered_end_points(self):
        return [self.parent_line.p2(), self.parent_line.p1()] if self.is_start else \
            [self.parent_line.p1(), self.parent_line.p2()]

    def itemChange(self, change, value):
        """
        Update line when the handle is moving
        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.ItemPositionChange:
            self.parent_line.set_visible_handles(False, non_check_handle=self)
            vertex_value = self.polygon().last() + value
            value_in_line = project_pixel_point_to_segment(self.parent_line.p1(), self.parent_line.p2(),
                                                           vertex_value, in_segment=False)
            self.parent_line.update_line_end_point(self.is_start, value_in_line)
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        self.parent_line.set_visible_handles(False)
        self.parent_line.stick_to_line_handles()
        super().mouseReleaseEvent(event)


class RotateHandle(QGraphicsEllipseItem):
    """
    Handle to rotate a line around one of its end points
    """
    def __init__(self, parent_line, is_start, scale_factor, percentage=0.8, size=(-5, -5, 10, 10),
                 color=(255, 255, 255)):
        super().__init__(size[0], size[1], size[2], size[3])
        self.is_start     = is_start
        self.parent_line  = parent_line
        self.scale_factor = scale_factor
        self.percentage   = percentage

        self.setBrush(QColor(color[0], color[1], color[2]))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)  # to send itemChange events
        self.setParentItem(parent_line)

        self.move_to_line()

        self.setVisible(False)  # handles only appears when parent object is selected

    def move_to_line(self):
        pp1, pp2 = self.ordered_end_points()
        pp3      = get_point_at_t_pixels(pp1, pp2, t=self.percentage)
        self.setPos(pp3)

    def ordered_end_points(self):
        return [self.parent_line.p2(), self.parent_line.p1()] if self.is_start else \
            [self.parent_line.p1(), self.parent_line.p2()]

    def non_selected_end_point(self):
        return self.parent_line.p2() if self.is_start else self.parent_line.p1()

    def itemChange(self, change, value):
        """
        Update line when the circle is moving
        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.ItemPositionChange:
            self.parent_line.set_visible_handles(False, non_check_handle=self)
            length = self.parent_line.length_in_pixels()
            pp1    = self.non_selected_end_point()
            p1, p2 = pixel_points_to_point([pp1, value])
            p3     = point_between_points_at_distance(p1, p2, length)
            pp3    = point_to_pixel_point(p3, 1.0)
            self.parent_line.update_line_end_point(self.is_start, pp3)
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        self.parent_line.set_visible_handles(False)
        self.parent_line.stick_to_line_handles()
        super().mouseReleaseEvent(event)


# auxiliary functions
def get_arrow_head(start_point, end_point, size=10, percentage=0.9):
    """
    Returns the head of an arrow aligned with line (start_point, end_point) with the point of the arrow is end_point
    :param start_point:
    :param end_point:
    :param size: size of each side of the arrow
    :param percentage: percentage of the line the arrow head will occupy
    :return:
    """
    p1, p2     = pixel_points_to_point([start_point, end_point])
    p90        = get_point_at_t(p1, p2, percentage)
    per_points = perpendicular_points_from_segment(p1, p90, size)

    points = [QPointF(p[0], p[1]) for p in per_points]
    points.append(end_point)  # order is important, this should be last
    return QPolygonF(points)


def scale(distance, scale_factor):
    """
    Useful to transform a value in meters to a value in pixels
    :param distance: :type float
    :param scale_factor:
    :return: :type int
    """
    return distance * scale_factor


def de_scale(distance, scale_factor):
    """
    Useful to transform a value in pixels to a value in meters
    :param distance: :type int
    :param scale_factor:
    :return: :type float
    """
    return float(distance / scale_factor)


def point_to_pixel_point(point, scale_factor):
    return QPointF(scale(point[0], scale_factor), scale(point[1], scale_factor))


def pixel_point_to_point(q_point, scale_factor, translate):
    return [de_scale(q_point.x() + translate.x(), scale_factor), de_scale(q_point.y() + translate.y(), scale_factor)]


def pixel_points_to_point(pixel_points, scale_factor=1.0, translate=None):
    """
    Convinient form to get point from pixel points at once
    :param pixel_points:
    :param scale_factor:
    :param translate:
    :return:
    """
    translate1 = translate if translate is not None else QPointF(0, 0)
    return [pixel_point_to_point(pp, scale_factor, translate1) for pp in pixel_points]


def distance_in_pixels(p1, p2):
    return math.hypot(p1.x()-p2.x(), p1.y()-p2.y())


def project_pixel_point_to_segment(pp1, pp2, pp3, in_segment=False):
    p1, p2, p3 = pixel_points_to_point([pp1, pp2, pp3])
    p4 = project_point_to_segment(p1, p2, p3, in_segment=in_segment)
    return QPointF(p4[0], p4[1])


def get_point_at_t(p1, p2, t):
    """
    Given a t in the parametric equation, returns the corresponding point in the line
    See: http://www.nabla.hr/PC-ParametricEqu1.htm
    :param p1: start point
    :param p2: end point
    :param t:
    :return: [x, y]
    """
    x = p1[0] + (p2[0] - p1[0]) * t
    y = p1[1] + (p2[1] - p1[1]) * t
    return [x, y]


def get_point_at_t_pixels(pp1, pp2, t):
    """
    Same as get_point_at_t but all point are pixel points
    :param pp1:
    :param pp2:
    :param t:
    :return:
    """
    p1, p2 = pixel_points_to_point([pp1, pp2])
    p3     = get_point_at_t(p1, p2, t)
    return point_to_pixel_point(p3, 1.0)


def point_in_line_at_distance(a, point, d, sign):
    """
    Return a new point in line with coefficient a and passing by point, separated d from it
    given there are 2 points that meet the criteria, sign defines which one
    :param a:
    :param point:
    :param d:
    :param sign:
    :return:
    """
    x1, y1 = point
    x2     = x1 + sign*d/math.sqrt(1 + a*a)
    y2     = a*(x2 - x1) + y1
    return x2, y2


def perpendicular_points_from_segment(p1, p2, d):
    """
    Given a segment defined by 2 points, returns the 2 points who are perpendicular to segment in p2 and separated
    d from it
    formula:
    https://math.stackexchange.com/questions/175896/finding-a-point-along-a-line-a-certain-distance-away-from-another-point
    :param p1: start of segment :type [x, y]
    :param p2: end of segment :type [x, y]
    :param d:
    :return: list of points
    """

    (x2, y2) = p2

    if is_horizontal_line(p1, p2):
        return [(x2, y2 + d), (x2, y2 - d)]
    elif is_vertical_line(p1, p2):
        return [(x2 + d, y2), (x2 - d, y2)]

    a, _ = line_slope_equation(p1, p2)
    a90  = perpendicular_slope(a)

    # find target points, in the line before, separated d from p2
    p3s = [point_in_line_at_distance(a90, (x2, y2), d, sign1) for sign1 in [-1, 1]]
    return p3s


def point_between_points_at_distance(p1, p2, d, precision=0.01):
    # returns a point in line with (p1, p2) separated d from p1
    (x1, y1) = p1
    (x2, y2) = p2

    x_sign = relation_sign(x1, x2)

    if similar_values(y1, y2, precision=precision):
        return x1 + x_sign*d, y1
    elif similar_values(x1, x2, precision=precision):
        return x1, y1 + relation_sign(y1, y2)*d

    a  = (y2 - y1)/(x2 - x1)
    p3 = point_in_line_at_distance(a, p1, d, x_sign)
    return p3


def relation_sign(x1, x2):
    if x1 < x2:
        return 1
    elif x1 > x2:
        return -1
    else:
        return 0


def similar_values(l1, l2, precision=0.08):
    return abs(l1 - l2) <= precision


def project_point_to_segment(p1, p2, p3, in_segment=True):
    """
    Given a segment defined by p1,p2 returns the projection of p3 on it
    source: https://stackoverflow.com/questions/849211/shortest-distance-between-a-point-and-a-line-segment
            answer 3:
    :param p1:
    :param p2:
    :param p3:
    :param in_segment: whether project only to segment (True) or in the whole line (False)
                       if True then if the projection point is outside the segment returns the closest segment end point
    :return: point :type [x, y]
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    px     = x2-x1
    py     = y2-y1

    d2 = px*px + py*py
    if abs(d2) < 0.0001:
        # segment too short (p1, p2)
        return p1

    u = ((x3 - x1) * px + (y3 - y1) * py) / float(d2)

    if in_segment:
        if u > 1:
            u = 1
        elif u < 0:
            u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3

    return x3 + dx, y3 + dy


def perpendicular_slope(slope):
    """
    Returns a slope perpendicular to the one given
    Note: a perpendicular line of a vertical line is horizontal
    :param slope: an angle representing the slope of a line
    :return: :type float
    """
    return -1 / slope if abs(slope) > 0.00001 else float('inf')


def line_slope_equation(p1, p2, near_zero_value=0.0001):
    """
    Returns the parameters of the line slope equation of a line for two given points
    EQ: y = a*x + b
    if line is vertical 'a' is None
    :param near_zero_value: small value used to check for zero with type float
    :param p1:
    :param p2:
    :return: a, b
    """
    diff_xs = p2[0] - p1[0]
    diff_ys = p2[1] - p1[1]
    if abs(diff_xs) < near_zero_value:  # safe way to check 0 with float
        a = None
        if abs(diff_ys) < near_zero_value:
            # both points are the same, no line can be defined
            b = None
        else:
            # it's a vertical line
            b = p2[0]
    else:
        a = float(diff_ys)/diff_xs
        b = p1[1] - a*p1[0]
    return a, b


def is_vertical_line(p1, p2):
    (x1, _) = p1
    (x2, _) = p2
    return near_zero(x1 - x2)


def is_horizontal_line(p1, p2):
    (_, y1) = p1
    (_, y2) = p2
    return near_zero(y1 - y2)


def near_zero(number, precision=0.001):
    return abs(number) < precision
