import unittest

from tern.analyze.common import get_package_files
from tern.classes.file_data import FileData


class TestCommon(unittest.TestCase):
    def testGetPackageFiles(self):
        fd1 = FileData('a.txt', 'usr/a.txt')
        fd2 = FileData('b.txt', 'lib/b.txt')
        layer_file_list = [fd1, fd2]

        pkg_dict = {
            'files': ['/usr/a.txt',
                      '/lib/b.txt']
        }

        get_package_files(layer_file_list, pkg_dict)
        self.assertEqual(pkg_dict['files'], [[fd1], [fd2]])
