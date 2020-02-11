import unittest
from tern.utils.general import check_image_string


class TestUtilGeneral(unittest.TestCase):

    def testImageString(self):
        correct_strings = [
            'image@digest_type:digest',
            'image:tag',
            'debian:buster',
            'golang:1.12-alpine',
            'p12/test@sha256:737aaa0caf3b8f64baa41ebf78c6cd0c43f34fadccc1275a32b8ab5d5b75c344'
        ]

        incorrect_strings = [
            'debian',
            'image',
            'debian@sha',
            'test/v1.56'
        ]

        for image_str in correct_strings:
            self.assertTrue(check_image_string(image_str))

        for image_str in incorrect_strings:
            self.assertFalse(check_image_string(image_str))
