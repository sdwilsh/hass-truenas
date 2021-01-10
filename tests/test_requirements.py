import json
import os
import unittest
from typing import List, Tuple

import pkg_resources

CLIENT_LIBRARY = "aiotruenas-client"
MANIFEST_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "custom_components",
    "truenas",
    "manifest.json",
)
REQUIREMENTS_DEV_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "requirements-dev.txt"
)


class TestRequirements(unittest.TestCase):
    def test_aiotruenas_client_synced(self) -> None:
        manifest_version = [
            r[1] for r in self._get_manifest_data() if r[0] == CLIENT_LIBRARY
        ]
        requirements_dev_version = [
            r[1] for r in self._get_requirements_dev_data() if r[0] == CLIENT_LIBRARY
        ]
        self.assertEqual(
            manifest_version,
            requirements_dev_version,
            f"The version of {CLIENT_LIBRARY} must match in `manifest.json` and `requirements-dev.txt`",
        )

    def _get_manifest_data(self) -> List[Tuple[str, List[Tuple[str, str]]]]:
        with open(MANIFEST_FILE, "r") as manifest:
            requirements = json.load(manifest)["requirements"]
            return [
                (req.key, req.specs)
                for req in pkg_resources.parse_requirements(requirements)
            ]

    def _get_requirements_dev_data(self) -> List[Tuple[str, List[Tuple[str, str]]]]:
        with open(REQUIREMENTS_DEV_FILE, "r") as requirements:
            return [
                (req.key, req.specs)
                for req in pkg_resources.parse_requirements(requirements)
            ]


if __name__ == "__main__":
    unittest.main()
