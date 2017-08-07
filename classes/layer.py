class Layer(object):
    '''A representation of a Docker image layer
    attributes:
        sha: the sha256 of the layer filesystem
        packages: list of objects of type Package (package.py)
    methods:
        add: adds a package to the layer
        remove: removes a package from the layer'''
    def __init__(self, sha):
        self.__sha = sha
        self.__packages = []

    @property
    def sha(self):
        return self.__sha

    @property
    def packages(self):
        return self.__packages

    def add(self, package):
        self.__packages.append(package)

    def remove(self, package_name):
        rem_index = 0
        success = False
        for index in range(0, len(self.__packages)):
            if self.packages[index].name == package_name:
                rem_index = index
                success = True
                break
        if success:
            self.__packages.remove(self.__packages[rem_index])
        return success
