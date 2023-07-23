# Description
A simple, declarative oriented framework to create WinForms in Python.

While it can be used for all kinds of forms, it was created with the purpose of being applied in Robotics, where the need to visualize complex algorithms and, above all, observe the effect of parameter changes is very common.

The forms are defined in a declarative way in an YAML (layouts, widgets, toolbar, menus, etc.) and used in a Python program with just a few lines of code.

# How to use it
To create a WinForm it is necessary to create two files:
* a declaration file (*.yaml) that define the WinForm (menu bar, toolbar, layouts, widgets, etc.)
* a python file (with the same name) that handles all the WinForm logic (events, drawing, etc.)

For a complete form see `view_example.yaml` to understand how the form is defined and `view_example.py` how it is used.

If you run `python view_example.py` the form is: 

<img width="997" alt="winform_example" src="https://github.com/njodal/WIndow_form/assets/28706901/ab02ce1f-9409-454d-8d95-e130fe6d77ed">

In case a simple graph is needed look at `view_simple_graph.py`.
# Examples

## Form used to visualize a PID controller for control the speed of a car

<img width="999" alt="Screen Shot 2023-07-12 at 6 22 05 PM" src="https://github.com/njodal/WinDeklar/assets/28706901/93859f05-f9b6-4333-a451-34f5c302f8c1">



