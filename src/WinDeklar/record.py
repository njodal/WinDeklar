#!/usr/bin/env python

from __future__ import print_function

from datetime import datetime

import WinDeklar.yaml_functions as yaml


class Record:
    def __init__(self, file_name, dir='/tmp', indent=2, ext='yaml', add_time_stamp=True):
        self.file          = None       # only use file if something is going to be writing
        self.file_name     = file_name
        self.ext           = ext
        self.dir           = dir
        self.indent        = indent     # number of characters to indent in each level
        self.indent_spaces = ''
        self.add_ts        = add_time_stamp
        for _ in range(0, self.indent):
            self.indent_spaces += ' '

        self.file_name_ts = self.get_file_name_with_time_stamp()

        self.groups = {}
        self.opened = False

    def write_group(self, group_name, values, level=0, is_array=False):
        if values is None:
            # do nothing
            return
        if is_array:
            self.write_group_header(group_name, level)
        array_str = '- ' if is_array else ''
        front_str = level_spaces(level, self.indent_spaces)
        self.write_ln(front_str + array_str + group_name + ':')
        sub_spaces = front_str + self.indent_spaces
        if is_array:
            sub_spaces += self.indent_spaces
        for k, v in values.items():
            self.write_ln('%s%s: %s' % (sub_spaces, k, v))

    def write_group_header(self, group_name, level):
        if group_name not in self.groups:
            front_str = level_spaces(level - 1, self.indent_spaces)
            self.write_ln(front_str + group_name + 's:')
            self.groups[group_name] = True

    def write_ln(self, string):
        if not self.opened:
            self.file   = yaml.get_file_for_write(self.get_full_file_name())
            self.opened = True
            self.groups = {}
        self.file.write('%s\r\n' % string)

    def get_file_name_with_time_stamp(self):
        directory = '%s/' % self.dir if self.dir is not None else ''
        full_file_name = "%s%s" % (directory, self.file_name)
        if self.add_ts:
            now        = datetime.now()
            now_string = now.strftime("%Y_%m_%d_%H_%M_%S")  # ""%m/%d/%Y, %H:%M:%S"))
            full_file_name += '_%s' % now_string
        return full_file_name

    def get_full_file_name(self, with_ext=True):
        if self.file_name_ts is None:
            # get a new file name (needed when recording a behavior with more than 1000 steps because it is writen in
            # chunks)
            self.file_name_ts = self.get_file_name_with_time_stamp()
        if with_ext and yaml.file_name_extension(self.file_name) == '':
            # check if ext is present, if not add it
            full_file_name = '%s.%s' % (self.file_name_ts, self.ext)
        else:
            full_file_name = self.file_name_ts
        return full_file_name

    def close(self):
        if self.opened:
            self.opened = False
            self.file.close()
            self.file_name_ts = None


def level_spaces(level, indent_spaces):
    spaces = ''
    for _ in range(1, level+1):
        spaces += indent_spaces
    return spaces


if __name__ == "__main__":

    # just for testing
    r = Record('record_test.yaml')
    r.write_group('vehicle', {'l': 0.93, 'w': 0.7})
    r.write_ln('cycles:')
    r.write_group('cycle', {'age': 1, 'v': 2}, level=1, is_array=True)
    r.write_group('cycle', {'age': 2, 'v': 3}, level=1, is_array=True)
