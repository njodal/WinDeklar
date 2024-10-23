import math
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QUndoStack, \
    QGraphicsItem, QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsItemGroup, QGraphicsRectItem
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
        item.set_view(self)

    def add_items(self, items):
        for item in items:
            self.add_item(item)

    def delete_item(self, item):
        self.scene.removeItem(item)

    def delete_selected_items(self):
        for item in self.scene.selectedItems():
            self.delete_item(item)

    def clear(self):
        self.scene.clear()

    def remove_handles(self, non_check_handle=None):
        for handle in self.scene.items():
            if not isinstance(handle, Handle) or handle == non_check_handle:
                continue
            self.scene.removeItem(handle)
            del handle  # just to free memory
        self.scene.update()

    def selected_items(self):
        for item in self.view.scene.selectedItems():
            yield item

    # events
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            print("Right click")
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


class SceneItem(QGraphicsItemGroup):
    """
    Base class for any item in a scene, provides all the common functionality

    """
    is_movable_key    = 'is_movable'
    is_selectable_key = 'is_selectable'

    def __init__(self, item_def, scale_factor=100.0):
        """
        Super class to define an item that can be
        :param item_def:  item definition :type dict
        :param scale_factor: factor to convert from real values (usually meters) to pixels (number of pixels per meter)
        """
        # to avoid warning
        self.view = None

        self.scale_factor = scale_factor
        super().__init__()
        if item_def.get(self.is_movable_key, False):
            self.setFlag(QGraphicsItem.ItemIsMovable)
        if item_def.get(self.is_selectable_key, False):
            self.setFlag(QGraphicsItem.ItemIsSelectable)

        self.item_def = item_def
        self.name     = item_def.get('name', '')
        tooltip       = self.item_def.get('tooltip', self.name)
        if tooltip != '':
            self.setToolTip(tooltip)

        # flags
        # self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        # self.setFlag(QGraphicsItem.ItemIsSelectable)

        self.handles = []  # handles are created only when the item is clicked

    def set_view(self, view):
        self.view = view

    def end_resizing(self):
        """
        All housekeeping after resizing is finished
        :return:
        """
        self.remove_handles()

    # handles
    def set_handles(self):
        self.handles = self.get_handles()

    def remove_handles(self, non_check_handle=None):
        if self.view is None:
            return
        self.view.remove_handles(non_check_handle=non_check_handle)

    def get_handles(self):
        return []

    # events
    def mousePressEvent(self, event):
        """
        Make all handles visible, so the user can start manipulating the item
        :param event:
        :return:
        """
        # print('click on %s' % self.name)
        self.set_handles()
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        # print('mouse on %s' % self.name)
        super().hoverEnterEvent(event)


class SceneLine(SceneItem):
    def __init__(self, start_point, end_point, item_def, scale_factor=100.0):
        """
        Define a line
        :param start_point: in meters
        :param end_point:   in meters
        :param scale_factor: scale factor to convert to pixels
        """
        super().__init__(item_def, scale_factor=scale_factor)
        start_point_pixels = point_to_pixel_point(start_point, self.scale_factor)
        end_point_pixels   = point_to_pixel_point(end_point, self.scale_factor)
        self.line          = QGraphicsLineItem(QLineF(start_point_pixels, end_point_pixels))
        self.addToGroup(self.line)

    def p1(self):
        return self.line.line().p1()

    def p2(self):
        return self.line.line().p2()

    def central_point(self):
        return middle_pixel_point(self.p1(), self.p2())

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

    # update
    def update_line_end_point(self, is_start, new_pos):
        """
        Update one of the line end points depending on the is_start flag
        :param is_start: if True update start end point, else the other one
        :param new_pos:
        :return:
        """
        p1, p2 = [new_pos, self.p2()] if is_start else [self.p1(), new_pos]
        self.line.setLine(QLineF(p1, p2))

    def translate(self, translation):
        p1, p2 = [translate_pixel_point(p, translation) for p in [self.p1(), self.p2()]]
        self.line.setLine(QLineF(p1, p2))

    # handles
    def get_handles(self):
        handle_start      = ChangeEndPointHandle(self, True)     # enlarge start point
        handle_end        = ChangeEndPointHandle(self, False)    # enlarge end point
        handle_start_move = RotateHandle(self, True)      # rotate around end point
        handle_end_move   = RotateHandle(self, False)     # rotate around start point
        handle_move       = MoveHandle(self)              # move the whole item
        handles = [handle_start, handle_end, handle_start_move, handle_end_move, handle_move]
        return handles

    def __str__(self):
        return 'line %s,%s' % (self.start_point(), self.end_point())


class SceneCircle(SceneItem):
    def __init__(self, center_point, radius, item_def, scale_factor=100.0):
        """
        Define a circle
        :param center_point: in meters
        :param radius:   in meters
        :param scale_factor: scale factor to convert to pixels
        """
        super().__init__(item_def, scale_factor=scale_factor)
        center_pixels = point_to_pixel_point(center_point, self.scale_factor)
        radius_pixels = scale(radius, self.scale_factor)
        self.circle   = get_circle(center_pixels, radius_pixels)
        self.addToGroup(self.circle)

    def central_point(self):
        bounding_rect = self.circle.rect()
        return bounding_rect.center()

    def radius_pixels(self):
        bounding_rect = self.circle.rect()
        return bounding_rect.width() / 2

    def center(self):
        return pixel_point_to_point(self.central_point(), self.scale_factor, self.pos())

    def radius(self):
        return de_scale(self.radius_pixels(), self.scale_factor)

    # update
    def translate(self, translation):
        bounding_rect = self.circle.rect()
        self.circle.setRect(bounding_rect.x() + translation.x(), bounding_rect.y() + translation.y(),
                            bounding_rect.width(), bounding_rect.height())

    def update_radius(self, new_position):
        center     = self.central_point()
        new_radius = distance_in_pixels(center, new_position)
        # print(center, new_position, new_radius)
        self.circle.setRect(center.x() - new_radius, center.y() - new_radius, new_radius*2, new_radius*2)

    # handles
    def get_handles(self):
        handle_enlarge = ChangeSizeHandle(self)
        handle_move    = MoveHandle(self)              # move the whole item
        handles = [handle_enlarge, handle_move]
        return handles

    def __str__(self):
        return 'circle %s,%s' % (self.center(), self.radius())


class SceneCorridor(SceneItem):
    """
    A movable, resizable line
    """
    def __init__(self, start_point, end_point, width, item_def, scale_factor=100.0):
        """
        Define a line
        :param start_point: in meters
        :param end_point:   in meters
        :param scale_factor: scale factor to convert to pixels
        """
        super().__init__(item_def, scale_factor=scale_factor)

        self.width         = width
        start_point_pixels = point_to_pixel_point(start_point, self.scale_factor)
        end_point_pixels   = point_to_pixel_point(end_point, self.scale_factor)
        self.center_line   = QGraphicsLineItem(QLineF(start_point_pixels, end_point_pixels))
        pen                = QPen()
        pen.setStyle(Qt.DashLine)
        self.center_line.setPen(pen)
        self.border1 = QGraphicsLineItem()
        self.border2 = QGraphicsLineItem()

        self.update_borders()
        self.addToGroup(self.center_line)
        self.addToGroup(self.border1)
        self.addToGroup(self.border2)

    def p1(self):
        return self.center_line.line().p1()

    def p2(self):
        return self.center_line.line().p2()

    def central_point(self):
        return middle_pixel_point(self.p1(), self.p2())

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

    def get_borders_lines(self):
        p1, p2  = pixel_points_to_point([self.p1(), self.p2()])
        borders = parallel_segments(p1, p2, self.width/2)
        lines = [QLineF(point_to_pixel_point(start, 1.0), point_to_pixel_point(end, 1.0)) for [start, end] in borders]
        return lines

    # update
    def update_line_end_point(self, is_start, new_pos):
        """
        Update one of the line end points depending on the is_start flag
        :param is_start: if True update start end point, else the other one
        :param new_pos:
        :return:
        """
        p1, p2 = [new_pos, self.p2()] if is_start else [self.p1(), new_pos]
        self.center_line.setLine(QLineF(p1, p2))
        self.update_borders()

    def translate(self, translation):
        p1, p2 = [translate_pixel_point(p, translation) for p in [self.p1(), self.p2()]]
        self.center_line.setLine(QLineF(p1, p2))
        self.update_borders()

    def update_borders(self):
        """
        Make borders consistent with central line
        :return:
        """
        lines = self.get_borders_lines()
        self.border1.setLine(lines[0])
        self.border2.setLine(lines[1])

    # handles
    def get_handles(self):
        handle_start      = ChangeEndPointHandle(self, True)     # enlarge start point
        handle_end        = ChangeEndPointHandle(self, False)    # enlarge end point
        handle_start_move = RotateHandle(self, True)      # rotate around end point
        handle_end_move   = RotateHandle(self, False)     # rotate around start point
        handle_move       = MoveHandle(self)              # move the whole item
        handles = [handle_start, handle_end, handle_start_move, handle_end_move, handle_move]
        return handles

    def __str__(self):
        return 'line %s,%s' % (self.start_point(), self.end_point())


class Handle(QGraphicsItemGroup):
    """
    Base class for Handle associated to a parent item. Useful to enlarge, rotate, etc., the parent item
    """
    def __init__(self, parent_item):
        self.parent_item = parent_item

        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)  # to send itemChange
        # self.setParentItem(self.parent_item)
        self.parent_item.scene().addItem(self)

        self.move_to_parent()

    def move_to_parent(self):
        """
        Position the handle in the scene (depending on where the parent is)
        :return:
        """
        pass

    def update_parent(self, new_position):
        """
        Updates the parent position according to the handle new position
        :param new_position:
        :return:
        """
        pass

    def itemChange(self, change, value):
        """
        Update parent when the handle is moving
        :param change:
        :param value:
        :return:
        """
        if change == QGraphicsItem.ItemPositionChange:
            self.parent_item.remove_handles(non_check_handle=self)   # remove all others items
            self.update_parent(value)
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        """
        Finish the transformation
        :param event:
        :return:
        """
        self.parent_item.end_resizing()
        super().mouseReleaseEvent(event)


class ChangeEndPointHandle(Handle):
    """
    Handle to change one of the end points of a line
    """
    def __init__(self, parent_line, is_start, size=10, t=0.9, color=(255, 255, 255)):
        self.size         = size
        self.t            = t
        self.is_start     = is_start
        self.polygon      = QGraphicsPolygonItem()   # property initialed with move_to_parent
        self.polygon.setBrush(QColor(color[0], color[1], color[2]))

        super().__init__(parent_line)
        self.addToGroup(self.polygon)

    def move_to_parent(self):
        """
        Position the handle in the scene (depending on where the parent is)
        :return:
        """
        pp1, pp2 = self.ordered_end_points()
        polygon  = get_arrow_head(pp1, pp2, self.size, percentage=self.t)
        self.polygon = QGraphicsPolygonItem(polygon)

    def update_parent(self, new_position):
        """
        Updates the parent position according to the handle new position
        :param new_position:
        :return:
        """
        vertex_value = self.polygon.polygon().last() + new_position
        value_in_line = project_pixel_point_to_segment(self.parent_item.p1(), self.parent_item.p2(),
                                                       vertex_value, in_segment=False)
        self.parent_item.update_line_end_point(self.is_start, value_in_line)

    def ordered_end_points(self):
        return [self.parent_item.p2(), self.parent_item.p1()] if self.is_start else \
            [self.parent_item.p1(), self.parent_item.p2()]


class ChangeSizeHandle(Handle):
    """
    Handle to rotate a line around one of its end points
    """
    def __init__(self, parent_item, size=(-5, -5, 10, 10),
                 color=(255, 255, 255)):

        self.circle = QGraphicsEllipseItem(size[0], size[1], size[2], size[3])  # property initialed with move_to_parent
        self.circle.setBrush(QColor(color[0], color[1], color[2]))

        super().__init__(parent_item)
        self.addToGroup(self.circle)
        center = self.parent_item.central_point()
        radius = self.parent_item.radius_pixels()
        pp1    = QPointF(center.x() + radius, center.y())
        self.circle.setPos(pp1)

    def move_to_parent(self):
        pass

    def update_parent(self, new_position):
        """
        Updates the parent position according to the handle new position
        :param new_position: note that new_position is relative to parent
        :return:
        """
        self.circle.setPos(self.circle.pos() + new_position)
        self.parent_item.update_radius(self.circle.pos())


class MoveHandle(Handle):
    """
    Handle to move an item
    """
    def __init__(self, parent_item, size=10, color=(255, 255, 255)):
        self.size      = size
        self.rectangle = QGraphicsRectItem()  # property initialed with move_to_parent
        self.rectangle.setBrush(QColor(color[0], color[1], color[2]))

        super().__init__(parent_item)
        self.addToGroup(self.rectangle)

    def move_to_parent(self):
        """
        Position the handle in the scene (depending on where the parent is)
        :return:
        """
        pos            = self.parent_item.central_point()
        rectangle      = QRectF(pos.x()-self.size/2, pos.y()-self.size/2, self.size, self.size)
        self.rectangle = QGraphicsRectItem(rectangle)

    def update_parent(self, new_position):
        """
        Updates the parent position according to the handle new position
        :param new_position:
        :return:
        """
        self.parent_item.translate(difference_pixel_point(new_position, self.pos()))


class RotateHandle(Handle):
    """
    Handle to rotate a line around one of its end points
    """
    def __init__(self, parent_line, is_start, percentage=0.8, size=(-5, -5, 10, 10),
                 color=(255, 255, 255)):
        self.is_start   = is_start
        self.percentage = percentage

        self.circle = QGraphicsEllipseItem(size[0], size[1], size[2], size[3])  # property initialed with move_to_parent
        self.circle.setBrush(QColor(color[0], color[1], color[2]))

        super().__init__(parent_line)
        self.addToGroup(self.circle)

    def move_to_parent(self):
        pp1, pp2 = self.ordered_end_points()
        pp3      = get_point_at_t_pixels(pp1, pp2, t=self.percentage)
        self.circle.setPos(pp3)

    def update_parent(self, new_position):
        """
        Updates the parent position according to the handle new position
        :param new_position: note that new_position is relative to parent
        :return:
        """
        length = self.parent_item.length_in_pixels()
        pp1    = self.non_selected_end_point()
        pp2    = translate_pixel_point(self.circle.pos(), new_position)
        p1, p2 = pixel_points_to_point([pp1, pp2])
        p3     = point_between_points_at_distance(p1, p2, length)
        pp3    = point_to_pixel_point(p3, 1.0)
        self.parent_item.update_line_end_point(self.is_start, pp3)

    def ordered_end_points(self):
        return [self.parent_item.p2(), self.parent_item.p1()] if self.is_start else \
            [self.parent_item.p1(), self.parent_item.p2()]

    def non_selected_end_point(self):
        return self.parent_item.p2() if self.is_start else self.parent_item.p1()


def get_circle(center_point, radius):
    """
    Returns a circle
    :param center_point: :type QPointF
    :param radius: in pixels :type float
    :return:
    """
    x = center_point.x() - radius
    y = center_point.y() - radius
    width = radius
    height = radius
    return QGraphicsEllipseItem(x, y, width, height)


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
    Transform a value in meters to a value in pixels
    :param distance: :type float
    :param scale_factor:
    :return: :type int
    """
    return distance * scale_factor


def de_scale(distance, scale_factor):
    """
    Transform a value in pixels to a value in meters
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
    Convenient form to get point from pixel points at once
    :param pixel_points:
    :param scale_factor:
    :param translate:
    :return:
    """
    translate1 = translate if translate is not None else QPointF(0, 0)
    return [pixel_point_to_point(pp, scale_factor, translate1) for pp in pixel_points]


def distance_in_pixels(p1, p2):
    return math.hypot(p1.x()-p2.x(), p1.y()-p2.y())


def middle_pixel_point(p1, p2):
    return QPointF((p1.x()+p2.x())/2, (p1.y()+p2.y())/2)


def difference_pixel_point(p1, p2):
    return QPointF(p1.x()-p2.x(), p1.y()-p2.y())


def translate_pixel_point(p, translation):
    return QPointF(p.x()+translation.x(), p.y()+translation.y())


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


def rectangle_from_line(p1, p2, width):
    """
    Returns a rectangle (its four vertices) whose center line is p1,p2 with width 2*width
    :param p1:
    :param p2:
    :param width:
    :return:
    """
    p21, p22 = perpendicular_points_from_segment(p1, p2, width)
    p11, p12 = perpendicular_points_from_segment(p2, p1, width)
    return p21, p22, p12, p11


def parallel_segments(p1, p2, distance):
    """
    Returns the two segments parallel to segment p1, p2 at distance
    :param p1:
    :param p2:
    :param distance:
    :return:
    """
    p21, p22, p11, p12 = rectangle_from_line(p1, p2, distance)
    return [[p11, p22], [p12, p21]]


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
