import unittest
from tern.utils import general


class TestUtilGeneral(unittest.TestCase):

    def testImageString(self):
        correct_strings = [
            'image@digest_type:digest',
            'image:tag',
            'debian:buster',
            'golang:1.12-alpine',
            ('p12/test@sha256:737aaa0caf3b8f64baa41ebf78c6cd0c43f34fadccc1275'
             'a32b8ab5d5b75c344')
        ]

        incorrect_strings = [
            'debian',
            'image',
            'debian@sha',
            'test/v1.56'
        ]

        for image_str in correct_strings:
            self.assertTrue(general.check_image_string(image_str))

        for image_str in incorrect_strings:
            self.assertFalse(general.check_image_string(image_str))

    def testParseImageString(self):
        hello = 'hello-world'
        debian = 'debian:9.8-slim'
        distroless = 'gcr.io/distroless/static'
        resizer = 'gcr.io/google-containers/addon-resizer:2.3'
        etcd = ('bitnami/etcd@sha256:35862e29b27efd97cdf4a1fc79abc1341feac556'
                '32e4256b02e6cfee9a4b6455')
        nexus = ('nexus3.onap.org:10001/onap/so/so-oof-adapter@sha256:d7e1f739ba732c'
                 '853a638f9c90becd5e0f8d313c8d506567b0b83ac38a1d53cb')
        self.assertEqual(general.parse_image_string(hello),
                         {'name': 'hello-world',
                          'tag': '',
                          'digest_type': '',
                          'digest': ''})
        self.assertEqual(general.parse_image_string(debian),
                         {'name': 'debian',
                          'tag': '9.8-slim',
                          'digest_type': '',
                          'digest': ''})
        self.assertEqual(general.parse_image_string(distroless),
                         {'name': 'gcr.io/distroless/static',
                          'tag': '',
                          'digest_type': '',
                          'digest': ''})
        self.assertEqual(general.parse_image_string(resizer),
                         {'name': 'gcr.io/google-containers/addon-resizer',
                          'tag': '2.3',
                          'digest_type': '',
                          'digest': ''})
        self.assertEqual(general.parse_image_string(etcd),
                         {'name': 'bitnami/etcd',
                          'tag': '',
                          'digest_type': 'sha256',
                          'digest': ('35862e29b27efd97cdf4a1fc79abc1341fe'
                                     'ac55632e4256b02e6cfee9a4b6455')})
        self.assertEqual(general.parse_image_string(nexus),
                         {'name': 'nexus3.onap.org:10001/onap/so/so-oof-adapter',
                          'tag': '',
                          'digest_type': 'sha256',
                          'digest': ('d7e1f739ba732c853a638f9c90becd5e0f8'
                                     'd313c8d506567b0b83ac38a1d53cb')})


if __name__ == '__main__':
    unittest.main()
