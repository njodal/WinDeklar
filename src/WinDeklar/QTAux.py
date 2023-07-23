#!/usr/bin/env python

import sys
from PyQt5 import QtCore, QtWidgets, QtGui
from enum import IntEnum


def def_app(style='Plastique'):
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create(style))
    return app


# You need to set up a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very wrong ...
class Communicate(QtCore.QObject):
    data_signal = QtCore.pyqtSignal(list)


def set_button(name, width, height, layout, action):
    button = QtWidgets.QPushButton(name)
    set_custom_size(button, width, height)
    button.clicked.connect(action)
    layout.addWidget(button)
    return button


def set_label(name, layout, height=None, width=None):
    label = QtWidgets.QLabel(name)
    label.setAlignment(QtCore.Qt.AlignCenter)
    if height is not None:
        label.setFixedHeight(height)
    if width is not None:
        label.setFixedWidth(height)
    layout.addWidget(label)
    return label


def set_window(window, title, size):
    [new_x, new_y, width, height] = size
    window.setGeometry(new_x, new_y, width, height)
    window.setWindowTitle(title)


def set_custom_size(x, width, height):
    size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    size_policy.setHorizontalStretch(0)
    size_policy.setVerticalStretch(0)
    size_policy.setHeightForWidth(x.sizePolicy().hasHeightForWidth())
    x.setSizePolicy(size_policy)
    x.setMinimumSize(QtCore.QSize(width, height))
    x.setMaximumSize(QtCore.QSize(width, height))


def set_progress_bar(host):
    return QtWidgets.QProgressBar(host)


class ScreenWidget(object):
    """
    Abstract class for any kind of screen widget like Sliders and Combos
    """

    def __init__(self, name, title, bound, action, layout, tooltip=None, label_height=20):
        # bound is the object responsible to keep the value, must implement:
        #     get_value
        #     set_widget_value
        self.name    = name
        self.ename   = title
        self.bounded = bound
        self.action  = action
        self.label   = None

        # print('widget:%s bound:%s, action:%s' % (name, bound, action))

        self.bounded_name = 'self.bounded.'
 
        widget = self.get_widget()
        if widget is not None and layout is not None:
            title = self.title()
            if title != '':
                self.label = set_label(title, layout, height=label_height)  # must go after slider (see title())
            layout.addWidget(widget)
            if tooltip is not None:
                widget.setToolTip(tooltip)

        self.refresh_others = False
        self.refresh()

    def current_value(self):
        return self.bounded.get_value(self.name)

    def title(self):
        return self.ename

    def changed(self):
        """
        Internal event triggered when user changes the widget on the form, does the following things:
            - updates the internal value
            - trigger any user defined action (useful for recalculate other values for example)
        :return:
        """
        # print('%s changed to %s (bounded:%s)' % (self.name, self.value(), self.bounded))
        self.bounded.set_value(self.name, self.value())
        self.exec_action()

    def exec_action(self):
        self.exec_bounded_method(self.action)

    def exec_bounded_method(self, method_name):
        if method_name is None or method_name == '':
            return
        return getattr(self.bounded, method_name)()

    def get_widget(self):
        # abstract method
        return None

    def value(self):
        # abstract method
        return 0

    def refresh(self):
        # abstract method
        pass

    def set_ename(self, new_ename):
        self.ename = new_ename

    def set_fixed_width(self, width):
        widget = self.get_widget()
        if widget is not None:
            widget.setFixedWidth(width)

    def set_visible(self, is_visible):
        widget = self.get_widget()
        if widget is None:
            return
        widget.setVisible(is_visible)
        if self.label is not None:
            self.label.setVisible(is_visible)


class EnumCombo(ScreenWidget):
    def __init__(self, name, title, bound, enum, action, layout, tooltip=None):
    
        self.enum  = enum
        self.combo = QtWidgets.QComboBox(None)
        for member in self.enum:
            self.combo.addItem(member.name)

        self.combo.currentIndexChanged.connect(self.changed_combo)

        super(EnumCombo, self).__init__(name, title, bound, action, layout, tooltip=tooltip)

    def current_value(self):
        e = self.bounded.get_value(self.name)
        return e  # e.value

    def value(self):
        value = self.enum(self.combo.currentIndex())
        return value

    def refresh(self):
        self.combo.setCurrentIndex(self.current_value())

    def changed_combo(self, i):
        self.bounded.set_value(self.name, self.enum(i))
        self.exec_action()

    def get_widget(self):
        return self.combo


class Combo(ScreenWidget):
    def __init__(self, name, title, bound, action, layout, widget_def, tooltip=None, values_key='values'):
        self.combo = QtWidgets.QComboBox(None)

        self.combo.currentTextChanged.connect(self.changed)
        super(Combo, self).__init__(name, title, bound, action, layout, tooltip=tooltip)

        original_values         = []
        self.load_values_action = None
        if values_key in widget_def:
            values1 = widget_def[values_key]
            if isinstance(values1, list):
                original_values = values1
            else:
                load_function = string_to_eval(values1)
                if load_function is not None:
                    self.load_values_action = load_function
        self.set_values(original_values)  # must go after definition so self.bounded_name exists

    def set_values(self, values):
        self.combo.clear()
        values1 = self.exec_bounded_method(self.load_values_action) if self.load_values_action is not None else values
        self.combo.addItems(values1)

    def value(self):
        return self.combo.currentText()

    def get_widget(self):
        return self.combo

    def refresh(self):
        # print('current value: %s of %s' % (self.current_value(), self.name))
        self.combo.setCurrentText(self.current_value())


class Slider(ScreenWidget):
    def __init__(self, name, title, bound, min_value, max_value, action, layout, tooltip=None, scale=1):

        # Widget must be created before calling super
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.set_min_max(min_value, max_value)
        self.vfactor = scale
        self.action  = action
        
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        interval = (max_value - min_value)/10
        self.slider.setTickInterval(interval)

        self.slider.valueChanged.connect(self.changed)

        super(Slider, self).__init__(name, title, bound, action, layout, tooltip=tooltip)

    def title(self):
        return '%s(%s)' % (self.ename, self.value())

    def changed(self):
        # print('set %s' % self.name)
        self.bounded.set_value(self.name, self.value())
        self.label.setText(self.title())
        self.exec_action()

    def get_widget(self):
        return self.slider

    def value(self):
        value = float(self.slider.value())/self.vfactor  # integer to float scaling (slider only accept integers)
        return value

    def refresh(self):
        self.slider.setValue(self.current_value()*self.vfactor)

    def set_min_max(self, min_value, max_value):
        # print('set min:%s max:%s' % (min_value, max_value))
        self.slider.setMinimum(min_value)
        self.slider.setMaximum(max_value)


class Button(ScreenWidget):
    def __init__(self, name, title, bound, action, layout, tooltip=None, width=50, length=100):

        # Widget must be created before calling super
        self.button = set_button(title, length, width, layout, self.changed)
        super(Button, self).__init__(name, title, bound, action, layout, tooltip=tooltip)

    def title(self):
        return ''  # button don't have title label

    def changed(self):
        # print '%s clicked (%s)' %(self.name, self.event)
        self.exec_action()

    def get_widget(self):
        return self.button

    def set_ename(self, new_ename):
        self.ename = new_ename
        self.button.setText(self.ename)


class CheckButton(ScreenWidget):
    def __init__(self, name, title, bound, action, layout, tooltip=None):

        # Widget must be created before calling super
        self.button = QtWidgets.QCheckBox(title)
        super(CheckButton, self).__init__(name, title, bound, action, layout, tooltip=tooltip)
        self.button.stateChanged.connect(self.changed)
        self.button.setChecked(self.current_value())

    def title(self):
        return ''  # button don't have title label

    def value(self):
        return self.button.isChecked()

    def get_widget(self):
        return self.button

    def refresh(self):
        self.button.setChecked(self.current_value())


class EditText(ScreenWidget):
    def __init__(self, name, title, bound, action, layout, tooltip=None):
        # Widget must be created before calling super
        self.edit_text = QtWidgets.QLineEdit()
        self.edit_text.textChanged.connect(self.changed)
        super(EditText, self).__init__(name, title, bound, action, layout, tooltip=tooltip)

    def get_widget(self):
        return self.edit_text

    def value(self):
        value = self.edit_text.text()
        return value

    def refresh(self):
        self.edit_text.setText(str(self.current_value()))


class EditNumber(ScreenWidget):
    def __init__(self, name, title, bound, action, layout, tooltip=None):
        # Widget must be created before calling super
        self.edit_text = QtWidgets.QLineEdit()
        self.edit_text.setValidator(QtGui.QDoubleValidator())
        self.edit_text.textChanged.connect(self.changed)
        super(EditNumber, self).__init__(name, title, bound, action, layout, tooltip=tooltip)

    def get_widget(self):
        return self.edit_text

    def value(self):
        value = float(self.edit_text.text())
        return value

    def refresh(self):
        self.edit_text.setText(str(self.current_value()))


class EditNumberSpin(ScreenWidget):
    def __init__(self, name, title, bound, action, layout, widget_def, tooltip=None, parms_def='parms',
                 step_def='step', type_def='type', min_def='minimum', max_def='maximum'):
        # Widget must be created before calling super
        parms = widget_def.get(parms_def, {})
        is_integer = parms.get(type_def, 'float') == 'integer'
        self.edit_spin = QtWidgets.QSpinBox(None) if is_integer else QtWidgets.QDoubleSpinBox(None)
        if step_def in parms:
            self.edit_spin.setSingleStep(parms[step_def])
        if min_def in parms:
            self.edit_spin.setMinimum(parms[min_def])
        if max_def in parms:
            self.edit_spin.setMaximum(parms[max_def])
        self.edit_spin.valueChanged.connect(self.changed)
        super(EditNumberSpin, self).__init__(name, title, bound, action, layout, tooltip=tooltip)

    def get_widget(self):
        return self.edit_spin

    def value(self):
        value = float(self.edit_spin.value())
        return value

    def refresh(self):
        self.edit_spin.setValue(self.current_value())

    def set_min_max(self, min_value, max_value):
        # print('set min:%s max:%s' % (min_value, max_value))
        self.edit_spin.setMinimum(min_value)
        self.edit_spin.setMaximum(max_value)


class MenuItem(ScreenWidget):
    def __init__(self, name, title, bound, action, layout, main_window, tooltip=None):
        # Widget must be created before calling super
        self.menu_item = QtWidgets.QAction(title, main_window)
        if action is not None:
            self.menu_item.triggered.connect(self.changed)
        super(MenuItem, self).__init__(name, title, bound, action, layout, tooltip=tooltip)

    def get_widget(self):
        return self.menu_item


class Action(ScreenWidget):
    """
    Wrapper for a QtAction, useful
    """
    def __init__(self, name, title, provider, main_window, properties, tooltip=None, icon_key='icon'):
        self.name = name
        if icon_key in properties:
            std_icon_name = getattr(QtWidgets.QStyle, properties[icon_key])
            icon = main_window.style().standardIcon(std_icon_name)
            self.qt_action = QtWidgets.QAction(icon, title, main_window)
        else:
            self.qt_action = QtWidgets.QAction(title, main_window)

        if tooltip is not None:
            self.qt_action.setToolTip(tooltip)
        super(Action, self).__init__(name, title, provider, None, None, tooltip=None)

    def value(self):
        return self.ename

    def refresh(self):
        # print('refresh title:%s' % self.current_value())
        self.qt_action.setText(self.current_value())

    def set_ename(self, new_ename):
        self.ename = new_ename
        self.qt_action.setText(self.ename)


class Label(ScreenWidget):
    """
    Read only text (also known as Label)
    """
    def __init__(self, name, title, bound, action, layout, tooltip=None, align_left=True):

        # Widget must be created before calling super
        self.label_title = title
        self.text        = QtWidgets.QLabel(title)
        self.text.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        if align_left:
            self.text.setAlignment(QtCore.Qt.AlignLeft)
        bound.set_value_if_not_present(name, title)
        super(Label, self).__init__(name, title, bound, action, layout, tooltip=tooltip)

    def get_widget(self):
        return self.text

    def refresh(self):
        # print('current value:%s' % self.current_value())
        self.text.setText('%s' % self.current_value())


class ProgressBar(ScreenWidget):
    def __init__(self, name, bound, action, layout, tooltip=None):

        # Widget must be created before calling super
        self.progress_bar = QtWidgets.QProgressBar(None)
        super(ProgressBar, self).__init__(name, '', bound, action, layout, tooltip=tooltip)

    def get_widget(self):
        return self.progress_bar

    def get_maximum(self):
        return self.progress_bar.maximum()

    def get_value(self):
        return self.progress_bar.value()

    def set_max(self, max_value):
        self.progress_bar.setMaximum(max_value)
        self.progress_bar.setVisible(True)

    def set_value(self, value):
        self.progress_bar.setValue(value)

    def add_increment(self, increment):
        self.progress_bar.setValue(self.get_value()+increment)

    def set_visible(self, value):
        self.progress_bar.setVisible(value)

    def reset(self):
        self.progress_bar.reset()


class Constant(ScreenWidget):
    def __init__(self, name, title, bound, action, layout, tooltip=None):
        # it doesn't show anything, it is used for executing actions at initialization time
        super(Constant, self).__init__(name, title, bound, action, layout, tooltip=tooltip)
        self.cte_value = self.current_value()
        self.exec_action()

    def value(self):
        return self.cte_value

    def get_widget(self):
        """
        Constant don't have an associated widget
        :return:
        """
        return None


class Menu:
    """
    Create a contextual menu to be showed via .popup()
    """
    def __init__(self, parent, title='Menu', actions=()):
        """
        :param parent:
        :param title:
        :param actions: list of [action_name, function_to_call]
        """
        self.menu = QtWidgets.QMenu(title, parent=parent)
        for [name, event] in actions:
            action = self.menu.addAction(name)
            action.triggered.connect(event)

    def popup(self):
        cursor = QtGui.QCursor()
        self.menu.popup(cursor.pos())


def string_to_eval(v):
    """
    Check if v is a string to the type '= ...', if not returns false,
    if true returns the string without the = (so it can be evaluated directly)
    :param v:
    :return:
    """
    return v[1:] if isinstance(v, str) and v[0] == '=' else None


class MouseButton(IntEnum):
    Left  = 1
    Right = 3
