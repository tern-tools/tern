# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 VMware, Inc. All Rights Reserved.
# SPDX-License-Identifier: BSD-2-Clause

import unittest

from tern.analyze.docker import dockerfile


class TestAnalyzeDockerDockerfile(unittest.TestCase):

    def setUp(self):
        self.buildpack = 'tests/dockerfiles/buildpack_deps_jessie_curl'
        self.buildpackpinned = 'tests/dockerfiles/buildpack_deps_jessie_pinned'
        self.golang = 'tests/dockerfiles/golang_1.13_stretch'
        self.buildpackarg = 'tests/dockerfiles/buildpack_deps_jessie_arg'

    def tearDown(self):
        del self.buildpack
        del self.golang
        del self.buildpackarg

    def testDockerfileObject(self):
        dfobj = dockerfile.Dockerfile()
        self.assertTrue(dfobj.is_none())

    def testDockerfileParserWithoutEnv(self):
        dfobj = dockerfile.get_dockerfile_obj(self.buildpack)
        self.assertFalse(dfobj.is_none())
        self.assertEqual(dfobj.parent_images, ['debian:jessie'])
        structure = [{'instruction': 'FROM',
                      'startline': 0,
                      'endline': 0,
                      'content': 'FROM debian:jessie\n',
                      'value': 'debian:jessie'},
                     {'instruction': 'RUN',
                      'startline': 2,
                      'endline': 7,
                      'content': ('RUN apt-get update && apt-get install -y --'
                                  'no-install-recommends \\\n\t\tca-certific'
                                  'ates \\\n\t\tcurl \\\n\t\tnetbase \\\n\t\tw'
                                  'get \\\n\t&& rm -rf /var/lib/apt/lists/*'
                                  '\n'),
                      'value': ('apt-get update && apt-get install -y --no-in'
                                'stall-recommends \t\tca-certificates \t\tcur'
                                'l \t\tnetbase \t\twget \t&& rm -rf /var/lib/'
                                'apt/lists/*')},
                     {'instruction': 'RUN',
                      'startline': 9,
                      'endline': 17,
                      'content': ('RUN set -ex; \\\n\tif ! command -v gpg > /'
                                  'dev/null; then \\\n\t\tapt-get update; \\'
                                  '\n\t\tapt-get install -y --no-install-reco'
                                  'mmends \\\n\t\t\tgnupg \\\n\t\t\tdirmngr \\'
                                  '\n\t\t; \\\n\t\trm -rf /var/lib/apt/lists/'
                                  '*; \\\n\tfi\n'),
                      'value': ('set -ex; \tif ! command -v gpg > /dev/null; t'
                                'hen \t\tapt-get update; \t\tapt-get install -'
                                'y --no-install-recommends \t\t\tgnupg \t\t\td'
                                'irmngr \t\t; \t\trm -rf /var/lib/apt/lists/*'
                                '; \tfi')}]
        self.assertEqual(dfobj.structure, structure)
        self.assertFalse(dfobj.envs)

    def testDockerfileParserWithEnv(self):
        dfobj = dockerfile.get_dockerfile_obj(self.buildpack,
                                              {'buildno': '123abc'})
        self.assertFalse(dfobj.is_none())
        self.assertEqual(dfobj.prev_env, {'buildno': '123abc'})

    def testReplaceEnv(self):
        dfobj = dockerfile.get_dockerfile_obj(self.golang)
        envs = {'GOLANG_VERSION': '1.13.6',
                'GOPATH': '/go',
                'PATH': '/go/bin:/usr/local/go/bin:'}
        self.assertEqual(dfobj.envs, envs)
        struct = dfobj.structure[9]
        dockerfile.replace_env(dfobj.envs, struct)
        self.assertEqual(struct['content'], 'WORKDIR /go\n')
        self.assertEqual(struct['value'], '/go')
        replace_content = ('\n\turl="https://golang.org/dl/go1.13.6.'
                           '${goRelArch}.tar.gz"; ')
        replace_value = (' \t\turl="https://golang.org/dl/go1.13.6'
                         '.${goRelArch}.tar.gz"')
        struct = dfobj.structure[5]
        dockerfile.replace_env(dfobj.envs, struct)
        self.assertEqual(struct['content'].split('\\')[14], replace_content)
        self.assertEqual(struct['value'].split(';')[28], replace_value)

    def testParseFromImage(self):
        dfobj = dockerfile.get_dockerfile_obj(self.buildpack)
        image_list = dockerfile.parse_from_image(dfobj)
        self.assertEqual(image_list, [{'name': 'debian',
                                       'tag': 'jessie',
                                       'digest_type': '',
                                       'digest': ''}])
        dfobj = dockerfile.get_dockerfile_obj(self.buildpackpinned)
        image_list = dockerfile.parse_from_image(dfobj)
        debian_digest = ('e25703ee6ab5b2fac31510323d959cdae31eebdf48e88891c54'
                         '9e55b25ad7e94')
        self.assertEqual(image_list, [{'name': 'debian',
                                       'tag': '',
                                       'digest_type': 'sha256',
                                       'digest': debian_digest}])

    def testExpandArg(self):
        dfobj = dockerfile.get_dockerfile_obj(self.buildpackarg)
        dockerfile.expand_arg(dfobj)
        replace_content = 'FROM debian:jessie\n'
        replace_value = 'debian:jessie'
        struct = dfobj.structure[1]
        self.assertEqual(struct['value'], replace_value)
        self.assertEqual(struct['content'], replace_content)


if __name__ == '__main__':
    unittest.main()
