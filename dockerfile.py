import re
'''
1. Read a provided Dockerfile and retrieve commands that would have
run during 'docker build' to create the docker image
2. For the docker directive RUN, retrieve the shell commands that were run
3. For the docker directive ENV, retrieve all the environment variables
'''

directives = ['FROM',
              'RUN',
              'ENV',
              'COPY',
              'ENTRYPOINT',
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
        if line_indent.match(line):
            command_cont = True
        else:
            command_cont = False

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
    return re.sub(cleaning, '', command)


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
