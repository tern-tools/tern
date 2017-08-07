class Package(object):
    '''A package installed within a Docker image layer
    attributes:
        name: package name
        version: package version
        license: package license
        src_url: package source url'''
    def __init__(self, name):
        self.__name = name
        self.__version = 0.0
        self.__license = ''
        self.__src_url = ''

    @property
    def name(self):
        return self.__name

    @property
    def version(self):
        return self.__version

    @version.setter
    def version(self, version):
        self.__version = version

    @property
    def license(self):
        return self.__license

    @license.setter
    def license(self, license):
        self.__license = license

    @property
    def src_url(self):
        return self.__src_url

    @src_url.setter
    def src_url(self, src_url):
        self.__src_url = src_url
