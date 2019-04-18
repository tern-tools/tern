#
# Copyright (c) 2019 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause
#

import unittest

from tern.classes.notice import Notice
from tern.classes.origins import Origins
from test_fixtures import TestTemplate2


class TestClassOrigins(unittest.TestCase):

    def setUp(self):
        self.notice_info = Notice("info")
        self.notice_warn = Notice("warning", "warning")
        self.notice_errr = Notice("error", "error")
        self.notice_hint = Notice("hint", "hint")

        self.origins = Origins()

    def tearDown(self):
        del self.notice_info
        del self.notice_warn
        del self.notice_errr
        del self.notice_hint
        del self.origins

    def testAddNoticeOrigin(self):
        self.assertFalse(len(self.origins.origins), 0)
        self.origins.add_notice_origin('origin_str')
        self.assertTrue(len(self.origins.origins), 1)
        self.assertEqual(self.origins.origins[0].origin_str, 'origin_str')

    def testAddNoticeToOrigins(self):
        # test new NoticeOrigin
        self.origins.add_notice_to_origins('origin_str', self.notice_info)
        self.assertEqual(len(self.origins.origins), 1)
        self.assertEqual(self.origins.origins[0].origin_str, 'origin_str')
        self.assertEqual(len(self.origins.origins[0].notices), 1)
        self.assertEqual(self.origins.origins[0].notices[0].message, 'info')
        self.assertEqual(self.origins.origins[0].notices[0].level, 'info')
        # test existing NoticeOrigin
        self.origins.add_notice_to_origins('origin_str', self.notice_warn)
        self.assertEqual(len(self.origins.origins), 1)
        self.assertEqual(len(self.origins.origins[0].notices), 2)
        self.assertEqual(self.origins.origins[0].notices[1].message, 'warning')
        self.assertEqual(self.origins.origins[0].notices[1].level, 'warning')

    def testGetOrigin(self):
        self.origins.add_notice_origin('origin_str')
        self.assertEqual(
            self.origins.get_origin('origin_str').origin_str, 'origin_str')

    def testIsEmpty(self):
        self.assertTrue(self.origins.is_empty())
        self.origins.add_notice_origin('origin_str')
        self.assertTrue(self.origins.is_empty())
        self.origins.add_notice_to_origins('origin_str', self.notice_errr)
        self.assertFalse(self.origins.is_empty())

    def testToDict(self):
        exp = [{
            'origin_str': 'origin_str1',
            'notices': [{
                'message': 'info',
                'level': 'info'
            }, {
                'message': 'warning',
                'level': 'warning'
            }]
        }, {
            'origin_str': 'origin_str2',
            'notices': [{
                'message': 'error',
                'level': 'error'
            }, {
                'message': 'hint',
                'level': 'hint'
            }]
        }]
        self.origins.add_notice_to_origins('origin_str1', self.notice_info)
        self.origins.add_notice_to_origins('origin_str1', self.notice_warn)
        self.origins.add_notice_to_origins('origin_str2', self.notice_errr)
        self.origins.add_notice_to_origins('origin_str2', self.notice_hint)
        self.assertEqual(self.origins.to_dict(), exp)

    def testToDictTemplate(self):
        exp = [{
            'note.source': 'origin_str1',
            'note.messages': [{
                'note.message': 'info',
                'note.level': 'info'
            }, {
                'note.message': 'warning',
                'note.level': 'warning'
            }]
        }, {
            'note.source': 'origin_str2',
            'note.messages': [{
                'note.message': 'error',
                'note.level': 'error'
            }, {
                'note.message': 'hint',
                'note.level': 'hint'
            }]
        }]
        template = TestTemplate2()
        self.origins.add_notice_to_origins('origin_str1', self.notice_info)
        self.origins.add_notice_to_origins('origin_str1', self.notice_warn)
        self.origins.add_notice_to_origins('origin_str2', self.notice_errr)
        self.origins.add_notice_to_origins('origin_str2', self.notice_hint)
        self.assertEqual(self.origins.to_dict(template), exp)


if __name__ == '__main__':
    unittest.main()
