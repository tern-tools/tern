'''
Copyright (c) 2018 VMware, Inc. All Rights Reserved.
SPDX-License-Identifier: BSD-2-Clause
'''

import unittest

from report import formats

from classes.notice import Notice
from classes.notice import NoticeException
from classes.notice_origin import NoticeOrigin


class TestClassNoticeOrigin(unittest.TestCase):

    def setUp(self):
        self.notice_info = Notice("info")
        self.notice_warn = Notice("warning", "warning")
        self.notice_errr = Notice("error", "error")
        self.notice_hint = Notice("hint", "hint")

        self.notices = [
            self.notice_info,
            self.notice_warn,
            self.notice_errr,
            self.notice_hint
        ]

        self.notice_origin = NoticeOrigin('origin_str')

    def tearDown(self):
        del self.notice_origin

    def testInstance(self):
        self.assertEqual(self.notice_origin.origin_str, 'origin_str')
        self.assertEqual(self.notice_origin.notices, [])

    def testAddNotice(self):
        exp = "Object type String, should be Notice"
        with self.assertRaises(AssertionError, msg=exp) as ex:
            self.notice_origin.add_notice("not_a_notice")

        self.notice_origin.add_notice(self.notice_info)
        self.assertEqual(len(self.notice_origin.notices), 1)
        self.notice_origin.add_notice(self.notice_errr)
        self.assertEqual(len(self.notice_origin.notices), 2)

    def testPrintNotices(self):
        self.notice_origin.add_notice(self.notice_info)
        self.assertEqual(
            self.notice_origin.print_notices(),
            formats.notice_format.format(
                origin="origin_str",
                info='info',
                warnings='',
                errors='',
                hints='')
        )

        self.notice_origin.add_notice(self.notice_warn)
        self.assertEqual(
            self.notice_origin.print_notices(),
            formats.notice_format.format(
                origin="origin_str",
                info='info',
                warnings='warning',
                errors='',
                hints='')
        )

        self.notice_origin.add_notice(self.notice_errr)
        self.assertEqual(
            self.notice_origin.print_notices(),
            formats.notice_format.format(
                origin="origin_str",
                info='info',
                warnings='warning',
                errors='error',
                hints='')
        )

        self.notice_origin.add_notice(self.notice_hint)
        self.assertEqual(
            self.notice_origin.print_notices(),
            formats.notice_format.format(
                origin="origin_str",
                info='info',
                warnings='warning',
                errors='error',
                hints='hint')
        )

    def testToDict(self):
        exp = {
            'origin_str': 'origin_str',
            'notices': [{
                'message': 'info',
                'level': 'info'
            }, {
                'message': 'warning',
                'level': 'warning'
            }, {
                'message': 'error',
                'level': 'error'
            }, {
                'message': 'hint',
                'level': 'hint'
            }]
        }
        for note in self.notices:
            self.notice_origin.add_notice(note)
        self.assertEqual(self.notice_origin.to_dict(), exp)


if __name__ == '__main__':
    unittest.main()
