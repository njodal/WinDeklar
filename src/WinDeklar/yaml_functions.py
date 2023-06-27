#!/usr/bin/env python

import os
import yaml
import json


def get_yaml_file(file_name, directory='', type='r', must_exist=True, verbose=False):
    if not file_name:
        print('No file name given')
        return
    if os.path.isabs(file_name):
        full_file_name = file_name
    else:
        if directory is None:
            script_dir = ''
        elif directory == '':
            script_dir = os.path.dirname(__file__) + '/'  # <-- absolute dir the script is in
        else:
            script_dir = directory + '/'
        full_file_name = script_dir + file_name

    try:
        with open(full_file_name, type) as yml_file:
            if verbose:
                print('Loading %s ...' % full_file_name)
            cfg = yaml.load(yml_file, Loader=yaml.FullLoader)
            if verbose:
                print('loaded')
    except IOError:
        cfg = {}
        if must_exist:
            raise Exception('File %s not found' % full_file_name)
    return cfg


def get_json_file(file_name, directory='', type='r', must_exist=True, verbose=False):
    if not file_name:
        print('No file name given')
        return
    if os.path.isabs(file_name):
        full_file_name = file_name
    else:
        if directory is None:
            script_dir = ''
        elif directory == '':
            script_dir = os.path.dirname(__file__) + '/'  # <-- absolute dir the script is in
        else:
            script_dir = directory + '/'
        full_file_name = script_dir + file_name

    try:
        with open(full_file_name, type) as json_file:
            if verbose:
                print('Loading %s ...' % full_file_name)
            cfg = json.load(json_file)  # Loader=yaml.FullLoader
            if verbose:
                print('loaded')
    except IOError:
        cfg = {}
        if must_exist:
            raise Exception('File %s not found' % full_file_name)
    return cfg


def save_yaml_file(dictionary, file_name, directory='', verbose=False):
    if not file_name:
        print('No file name given')
        return
    elif directory is None:
        script_dir = ''
    elif directory == '':
        script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    else:
        script_dir = directory
    full_file_name = script_dir + '/' + file_name

    with open(full_file_name, 'w') as f:
        yaml.dump(dictionary, f, default_flow_style=False)
        if verbose:
            print('saved to: %s' % full_file_name)
    return full_file_name


def save_json_file(dictionary, file_name, directory='', verbose=False):
    if not file_name:
        print('No file name given')
        return
    elif directory is None:
        script_dir = ''
    elif directory == '':
        script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    else:
        script_dir = directory
    full_file_name = script_dir + '/' + file_name

    with open(full_file_name, 'w') as f:
        json.dump(dictionary, f)
        if verbose:
            print('saved to: %s' % full_file_name)
    return full_file_name


def get_record(all_file, name, collection_name, record_name, key_name='name', alternative_key_name='desc'):
    # give a yaml file with a collection in it, returns one element of the collection with a given name
    # ex:
    #      tests:             # collection name
    #         - test:         # record name
    #             name:  xxx  # key_name: name
    if collection_name not in all_file:
        raise Exception('Collection %s not found in %s' % (collection_name, all_file))

    group_data = all_file[collection_name]
    for test_data in group_data:
        data = test_data[record_name]
        # print(data)
        if key_name in data:
            valid_key_name = key_name
        elif alternative_key_name in data:
            valid_key_name = alternative_key_name
        else:
            raise Exception('Nor key %s or %s present' % (key_name, alternative_key_name))
        if data[valid_key_name] == name:
            return data
    raise Exception('Name %s not found in %s' % (name, record_name))


def get_group_data(file_name, group_name, name='', key_name='name'):
    # Given a yaml FileName a group_name and a name, returns its data
    # ex: test.yaml, 'test', 'my test' return a group name 'test' in file test.yaml whose name is 'my test'
    #   if name is '' returns the first one
    #   'name' is configurable with key_name (ex: searching for 'external_name:' instead of 'name:'

    all_file = get_yaml_file(file_name)
    for definition in all_file:
        if group_name in definition:
            kvs = definition[group_name]
            if name == '':
                return kvs
            for key, value in kvs.items():
                if key == key_name and value == name:
                    return kvs

    not_found = '"- %s" group' % group_name if name == '' else '"- %s" named "%s"' % (group_name, name)
    raise Exception('%s does not exists in %s' % (not_found, file_name))


def get_all_names(file_name, group_name, key_name='name', key_description='description'):
    # given a file_name and group_name returns all the groups' name
    names = []
    all_file = get_yaml_file(file_name)
    for definition in all_file:
        if group_name in definition:
            kvs = definition[group_name]
            if key_name in kvs:
                desc = kvs[key_description] if key_description in kvs else ''
                names.append((kvs[key_name], desc))
    return names


def get_file_for_write(file_name, type='w+', directory=None):
    full_name = '%s/%s' % (directory, file_name) if directory is not None else file_name
    return open(full_name, type)


def string_to_dict(string):
    return yaml.safe_load(string)


def file_name_extension(file_name):
    """
    Returns the extension of the file name
    :param file_name:
    :return:
    """
    return os.path.splitext(file_name)[-1].lower()


def file_name_without_extension(file_name):
    """
    Returns the file name without the extension
    :param file_name:
    :return:
    """
    return os.path.splitext(file_name)[0] if file_name is not None else None


def directory_path(file_name):
    """
    Returns the directory path of a full file name
    :param file_name:
    :return:
    """
    return os.path.dirname(file_name)


def get_file_name_with_other_extension(file_path, ext='yaml'):
    dir_name      = os.path.dirname(os.path.abspath(file_path))
    base_name     = file_name_without_extension(os.path.basename(file_path))
    new_file_name = '%s/%s.%s' % (dir_name, base_name, ext)
    return new_file_name
