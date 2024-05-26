from collections import deque


class SignalHistory(object):
    """
    Store the last N values of a Signal
    """

    def __init__(self, length=10):
        self.length = length + 1
        self.values = None  # just to avoid warnings
        self.reset()

    def reset(self):
        self.values = deque(maxlen=self.length)

    def get_len(self):
        return self.length

    def set_len(self, length):
        """
        Changes the length of the queue
        Note: deletes the current values
        :param length:
        :return:
        """
        self.length = length + 1
        self.reset()

    def append(self, value):
        self.values.append(value)

    def update(self, value):
        """
        Change the last value
        :param value:
        :return:
        """
        # print 'before:%s v:%s' %(self.values, value)
        self.values.pop()
        self.values.append(value)
        # print 'after:%s' %(self.values)

    def load(self, values):
        """
        Bulk store values. Used to load from telemetry
        :param values:
        :return:
        """
        self.reset()
        for value in values:
            self.values.append(value)

    def is_full(self):
        return len(self.values) >= self.length

    def get_items_in_lifo_order(self):
        """
        Returns item in Last In - First Out order
        :return:
        """
        for i in range(len(self.values)-1, -1, -1):
            yield self.values[i]

    def get_items_in_fifo_order(self):
        """
        Returns item in First In - First Out order
        :return:
        """
        for v in self.values:
            yield v

    # aggregates
    def get_aggregate(self, aggregate_type):
        """
        Returns one of the implemented aggregates type, useful to test many kind of filters
        :param aggregate_type:
        :return:
        """
        if aggregate_type == 'last':
            return self.last()
        elif aggregate_type == 'average':
            return self.average()
        elif aggregate_type == 'min':
            return self.min()
        elif aggregate_type == 'max':
            return self.max()
        elif aggregate_type == 'sum':
            return self.sum()
        else:
            raise Exception('%s aggregate type not implemented' % aggregate_type)

    def last(self):
        return self.values[-1]

    def average(self):
        sum_v   = self.sum()
        count_v = len(self.values)
        if count_v > 0:
            # print 's:%s c:%s' %(sum_v, count_v)
            return float(sum_v)/count_v
        else:
            return 0

    def min(self):
        return min(self.values)

    def max(self):
        return max(self.values)

    def sum(self):
        # To Do: optimize to have the sum pre-calculated in every update
        return sum(self.values)

    def weighted_sum(self, weights, lifo_order=True):
        function = self.get_items_in_lifo_order if lifo_order else self.get_items_in_fifo_order
        total = 0.0
        for i, value in enumerate(function()):
            total += weights[i]*value
        return total
    # end aggregates

    def local_optimum_points(self):
        # returns the points where there are a local min or max
        dif = 0.1
        points = []
        for i in range(2, len(self.values)):
            d1 = self.values[i-1] - self.values[i-2]
            d2 = self.values[i]   - self.values[i-1]
            if d2 < -dif:
                if d1 > dif:
                    # local max
                    points.append((i, self.values[i-1], 1))  # 1 means max
            else:
                if d1 < -dif:
                    # local min
                    points.append((i, self.values[i-1], -1))  # -1 means min
        return points

    def changed_derivative(self):
        """
        Returns True if values changed derivative in the period
        :return: :type boolean
        """
        for i in range(2, len(self.values)):
            d1 = self.values[i-1] - self.values[i-2]
            d2 = self.values[i]   - self.values[i-1]
            if abs(d2-d1) > 0.1:  # not np.sign(d1) == np.sign(d2):
                # print 'd:%s' %(d2-d1)
                return True
        return False
