#!/usr/bin/env python3
#
# Designed and developed by 2026 ashtanko (Oleksii Shtanko)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Tests for unused (orphan) resource detection."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from localization import find_orphans  # noqa: E402


class OrphanTest(unittest.TestCase):
    """Exercise Kotlin and XML reference discovery."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self._write(
            "app/src/main/res/values/strings.xml",
            '<?xml version="1.0" encoding="utf-8"?>\n'
            "<resources>\n"
            '    <string name="used_in_kotlin">A</string>\n'
            '    <string name="used_in_xml">B</string>\n'
            '    <string name="never_used">C</string>\n'
            '    <string-array name="used_array"><item>x</item></string-array>\n'
            "</resources>\n",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def orphan_names(self) -> set[str]:
        return {orphan.resource_id.name for orphan in find_orphans(self.root)}

    def test_detects_only_unreferenced_keys(self) -> None:
        self._write(
            "app/src/main/kotlin/Screen.kt",
            "val a = stringResource(R.string.used_in_kotlin)\n"
            "val b = context.resources.getStringArray(R.array.used_array)\n",
        )
        self._write(
            "app/src/main/res/layout/screen.xml",
            '<TextView android:text="@string/used_in_xml" />\n',
        )

        self.assertEqual({"never_used"}, self.orphan_names())

    def test_all_unreferenced_when_no_source(self) -> None:
        self.assertEqual(
            {"used_in_kotlin", "used_in_xml", "never_used", "used_array"},
            self.orphan_names(),
        )

    def test_reference_only_in_tests_is_still_orphan(self) -> None:
        # src/test is not scanned; a production string used only by tests is unused.
        self._write(
            "app/src/test/kotlin/ScreenTest.kt",
            "val a = R.string.used_in_kotlin\n",
        )
        self.assertIn("used_in_kotlin", self.orphan_names())


if __name__ == "__main__":
    unittest.main()
