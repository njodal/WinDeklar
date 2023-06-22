class PointsBox:
    """
    Keeps an AABB that contains a set of points
       the box is creating adding points, but the points itself are not stored, just the min and max values
       of each coordinate
       AABB: Axis Aligned Bounding Box
    """

    def __init__(self, min_x=0.0, max_x=0.0, min_y=0.0, max_y=0.0):
        self.is_empty = True
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y

    def reset(self):
        self.is_empty = True

    def size(self):
        return self.min_x, self.max_x, self.min_y, self.max_y

    def add_points(self, points):
        """
        Use the points to update the box size
        :param points: :type list of [x, y]
        :return: nothing
        """
        for p in points:
            self.add_point(p)

    def add_point(self, p):
        [x, y] = p
        if self.is_empty:
            self.min_x, self.max_x, self.min_y, self.max_y = [x, x, y, y]
            self.is_empty = False
        else:
            self.min_x, self.max_x = update_bounds(x, self.min_x, self.max_x)
            self.min_y, self.max_y = update_bounds(y, self.min_y, self.max_y)

    def set_lim(self, ax, inc=1.1):
        min1 = min(self.min_x, self.min_y) * inc
        max1 = max(self.max_x, self.max_y) * inc
        ax.set_xlim([min1, max1])
        ax.set_ylim([min1, max1])

    def set_bounds(self, ax, inc=1.0):
        if self.is_empty:
            # defensive programming
            return
        ax.set_xbound(lower=add_inc(self.min_x, inc, -1), upper=add_inc(self.max_x, inc, 1))
        ax.set_ybound(lower=add_inc(self.min_y, inc, -1), upper=add_inc(self.max_y, inc, 1))

    def __str__(self):
        return 'min_x:%.2f max_x:%.2f min_y:%.2f max_y:%.2f' % (self.min_x, self.max_x, self.min_y, self.max_y)


def update_bounds(x, min_x, max_x):
    new_min_x = x if x < min_x else min_x
    new_max_x = x if x > max_x else max_x
    return new_min_x, new_max_x


def add_inc(value, inc, sign):
    """
    Returns a value bigger (by inc percentage) than itself taking in count the sign (negative must be less, positive
    greater
    :param value:
    :param inc:
    :param sign:
    :return:
    """
    delta = abs(value)*(inc - 1)
    return value + sign*delta
