# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#
"""
Dockerfile parser and information retrieval
"""

import re

directives = ['FROM',
              'ARG',
              'ADD',
              'RUN',
              'ENV',
              'COPY',
              'ENTRYPOINT',
              'WORKDIR',
              'VOLUME',
              'EXPOSE',
              'CMD']

# regex for matching lines in a dockerfile
comments = re.compile('^#')
line_indent = re.compile('.*\\\\$')
concatenation = re.compile('&&')
tabs = re.compile('\t')

# regex strings
cleaning = '[\t\\\\]'
bash_var = '[\$\{\}]'  # noqa

# strings
tag_separator = ':'


def get_command_list(dockerfile_name):
    '''Given a Dockerfile, return a list of Docker commands'''
    with open(dockerfile_name) as f:
        contents = f.read()
    dockerfile_lines = contents.split('\n')
    command_list = []
    command = ''
    command_cont = False
    for line in dockerfile_lines:
        # check if this line is a continuation of the previous line
        # it should not be a comment
        if command_cont:
            if comments.match(line):
                continue
            else:
                command = command + line
        # check if this line has an indentation
        # comments don't count
        command_cont = bool(line_indent.match(line))

        # check if there is a command or not
        if command == '':
            directive = line.split(' ', 1)[0]
            if directive in directives:
                command = line
        # check if there is continuation or not and if the command is still
        # non-empty
        if not command_cont and command != '':
            command_list.append(command)
            command = ''

    return command_list


def clean_command(command):
    '''Given a command string, clean out all whitespaces, tabs and line
    indentations
    Leave && alone'''
    return re.sub(cleaning, '', command).strip()


def get_directive(line):
    '''Given a line from a Dockerfile get the Docker directive
    eg: FROM, ADD, COPY, RUN and the object in the form of a tuple'''
    directive_and_action = line.split(' ', 1)
    return (directive_and_action[0], directive_and_action[1])


def get_directive_list(command_list):
    '''Given a list of docker commands extracted from a Dockerfile,
    provide a list of tuples containing the Docker directive
    i.e. FROM, ADD, COPY etc and the object to be acted upon'''
    directive_list = []
    for command in command_list:
        directive_list.append(get_directive(clean_command(command)))
    return directive_list


def get_base_instructions(instructions):
    '''Given a list of docker build instructions get a list of instructions
    related to the base instructions
    Possible docker instructions related to the base image:
        FROM <base image>

        FROM <image:tag>

        ARG <key value pair>
        FROM <key>

    Dockerfile rules say that the only instruction that can precede FROM is
    ARG'''
    base_instructions = []
    # check if the first instruction is FROM
    if instructions[0][0] == 'FROM':
        base_instructions.append(instructions[0])
    # check if the first instruction is ARG
    if instructions[0][0] == 'ARG':
        # collect all ARGS until FROM
        count = 0
        while instructions[count][0] != 'FROM':
            base_instructions.append(instructions[count])
            count = count + 1
        # get the form statement
        base_instructions.append(instructions[count])
    return base_instructions


def get_base_image_tag(base_instructions):
    '''Given the base docker instructions, return the base image and tag
    as a tuple
    This involves finding the ARG key value pair and then replacing it
    if it occurs in the image part
    NOTE: Dockerfile rules say that if no --build-arg is passed during
    docker build and ARG has no default, the build will fail. We assume
    for now that we will not be passing build arguments in which case
    if there is no default ARG, we will raise an exception indicating that
    since the build arguments are determined by the user we will not
    be able to determine what the user wanted'''
    # get all the ARG key-value pairs
    build_args = {}
    from_instruction = ''
    for instruction in base_instructions:
        if instruction[0] == 'FROM':
            from_instruction = instruction[1]
        else:
            key_value = instruction[1].split('=')
            # raise error if there is no default value
            if len(key_value) == 1:
                raise ValueError('No ARG default value.'
                                 ' Unable to determine base image')
            build_args.update({key_value[0]: key_value[1]})
    # replace any variables in FROM with value
    from_instruction = re.sub(bash_var, '', from_instruction)
    for key, value in build_args.items():
        from_instruction = from_instruction.replace(key, value)
    # check if the base image has a tag
    image_tag_list = from_instruction.split(tag_separator)
    if len(image_tag_list) == 1:
        image_tag_list.append('')
    return tuple(image_tag_list)
