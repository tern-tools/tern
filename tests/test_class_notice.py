#
# Copyright (c) 2017-2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import unittest

from tern.classes.notice import Notice
from tern.classes.notice import NoticeException


class TestClassNotice(unittest.TestCase):

    def setUp(self):
        self.notice = Notice()

    def tearDown(self):
        del self.notice

    def testInstance(self):
        self.assertFalse(self.notice.message)
        self.assertEqual(self.notice.level, 'info')

    def testSetters(self):
        self.notice.message = 'tag'
        self.assertEqual(self.notice.message, 'tag')
        with self.assertRaises(NoticeException):
            self.notice.level = 'something'
        self.notice.level = 'warning'

    def testGetters(self):
        self.notice.message = 'tag'
        self.notice.level = 'warning'
        self.assertEqual(self.notice.message, 'tag')
        self.assertEqual(self.notice.level, 'warning')

    def testToDict(self):
        self.notice.message = 'tag'
        self.notice.level = 'warning'
        dict = self.notice.to_dict()
        self.assertEqual(dict['message'], 'tag')
        self.assertEqual(dict['level'], 'warning')


if __name__ == '__main__':
    unittest.main()
