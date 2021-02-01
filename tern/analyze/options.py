class Options:
    '''A representation of user options
    attributes:
        shell: the shell found in the docker container
        redo: redo flag to repopulate the cache for found layers
        driver: required argument when running Tern in a container. If no
        input is provided, 'fuse' will be used as the default option.
    '''
    def __init__(self, shell, redo, driver=None):
        self.shell = shell
        self.redo = redo
        self.driver = driver
