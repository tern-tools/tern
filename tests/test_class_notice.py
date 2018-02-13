'''
Copyright (c) 2017 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import unittest

from classes.notice import Notice
from classes.notice import NoticeException


class TestClassNotice(unittest.TestCase):

    def setUp(self):
        self.notice = Notice()

    def tearDown(self):
        del self.notice

    def testInstance(self):
        self.assertFalse(self.notice.origin)
        self.assertFalse(self.notice.message)
        self.assertFalse(self.notice.level)

    def testSetters(self):
        self.notice.origin = 'FROM'
        self.assertEqual(self.notice.origin, 'FROM')
        self.notice.message = 'tag'
        self.assertEqual(self.notice.message, 'tag')
        with self.assertRaises(NoticeException):
            self.notice.level = 'something'
        self.notice.level = 'warning'

    def testGetters(self):
        self.notice.origin = 'FROM'
        self.notice.message = 'tag'
        self.notice.level = 'warning'
        self.assertEqual(self.notice.origin, 'FROM')
        self.assertEqual(self.notice.message, 'tag')
        self.assertEqual(self.notice.level, 'warning')


if __name__ == '__main__':
    unittest.main()
