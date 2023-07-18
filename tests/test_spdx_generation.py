import json
import os
import pickle
import unittest

from tern.classes.docker_image import DockerImage
from tern.formats.spdx.spdxjson.generator import SpdxJSON


class TestSPDXGeneration(unittest.TestCase):
    test_package = {
        "name": "alpine-keys",
        "SPDXID": "SPDXRef-alpine-keys-2.1-r2",
        "versionInfo": "2.1-r2",
        "supplier": "Organization: Alpine Linux",
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "MIT",
        "copyrightText": "NONE",
        "externalRefs": [
            {
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceLocator": "pkg:apk/alpine/alpine-keys@2.1-r2?arch=x86_64",
                "referenceType": "purl"
            }
        ],
        "comment": "alpine-keys:\n\twarning: No metadata for key: copyright\n\twarning: No metadata for key: download_url\n\twarning: No metadata for key: checksum\n\twarning: No metadata for key: pkg_licenses\n\twarning: No metadata for key: pkg_format\n\twarning: No metadata for key: src_name\n\twarning: No metadata for key: src_version\n"
    }

    test_describes_relationship = {
      "spdxElementId": "SPDXRef-DOCUMENT",
      "relatedSpdxElement": "SPDXRef-golang-1.12-alpine",
      "relationshipType": "DESCRIBES"
    }

    test_contains_relationship = {
      "spdxElementId": "SPDXRef-5216338b40",
      "relatedSpdxElement": "SPDXRef-alpine-keys-2.1-r2",
      "relationshipType": "CONTAINS"
    }

    test_has_prerequisite_relationship = {
      "spdxElementId": "SPDXRef-3957f7032f",
      "relatedSpdxElement": "SPDXRef-7306dca01e",
      "relationshipType": "HAS_PREREQUISITE"
    }

    test_extracted_licensing_info = {
      "extractedText": "MPL-2.0 GPL-2.0-or-later",
      "licenseId": "LicenseRef-f30c02b"
    }

    def test_spdx_generation_from_pickled_image(self):
        json_file_path = "spdx_test.json"
        test_image_file_path = "large_tern_scan_image.pkl"  # generated during "tern report -i golang:1.12-alpine"
        with open(test_image_file_path, "rb") as f:
            image = pickle.load(f)
        image_list = [image]

        json_as_string = SpdxJSON().generate(image_list, "SPDX-2.3")
        with open(json_file_path, "w") as f:
            f.write(json_as_string)

        with open(json_file_path, "r") as f:
            json_dict = json.load(f)
        assert json_dict["SPDXID"] == "SPDXRef-DOCUMENT"
        assert json_dict["spdxVersion"] == "SPDX-2.2"
        assert len(json_dict["packages"]) == 21
        assert self.test_package in json_dict["packages"]
        assert len(json_dict["relationships"]) == 25
        assert self.test_describes_relationship in json_dict["relationships"]
        assert self.test_contains_relationship in json_dict["relationships"]
        assert self.test_has_prerequisite_relationship in json_dict["relationships"]
        assert len(json_dict["hasExtractedLicensingInfos"]) == 4
        assert self.test_extracted_licensing_info in json_dict["hasExtractedLicensingInfos"]

        os.remove(json_file_path)


    def test_spdx_generation_from_docker_image(self):
        docker_image = DockerImage('vmware/tern@sha256:20b32a9a20752aa1ad7582c6'
                                   '67704fda9f004cc4bfd8601fac7f2656c7567bb4')

        json_as_string = SpdxJSON().generate([docker_image])
        i = 0