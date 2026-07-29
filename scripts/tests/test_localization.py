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
"""Tests for the repository localization tool."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import localization  # noqa: E402


class LocalizationTest(unittest.TestCase):
    """Exercise locale discovery, completeness, and formatter validation."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_resources(self, qualifier: str, body: str) -> None:
        directory = self.root / "feature/example/src/main/res" / qualifier
        directory.mkdir(parents=True)
        (directory / "strings.xml").write_text(
            f'<?xml version="1.0" encoding="utf-8"?>\n'
            f"<resources>{body}</resources>\n",
            encoding="utf-8",
        )

    def test_complete_locale_preserves_reordered_format_arguments(self) -> None:
        self.write_resources(
            "values",
            """
            <string name="welcome">%1$s has %2$d messages</string>
            <string name="brand" translatable="false">Example</string>
            """,
        )
        self.write_resources(
            "values-pt-rPT",
            """
            <string name="welcome">Há %2$d mensagens para %1$s</string>
            """,
        )

        issues, coverage = localization.check_repository(self.root)

        self.assertEqual([], issues)
        self.assertEqual({"pt-PT": (1, 1)}, coverage)

    def test_missing_resource_and_changed_format_type_fail(self) -> None:
        self.write_resources(
            "values",
            """
            <string name="count">Count: %1$d</string>
            <string name="missing">Translate me</string>
            """,
        )
        self.write_resources(
            "values-pt-rPT",
            """
            <string name="count">Contagem: %1$s</string>
            """,
        )

        issues, coverage = localization.check_repository(
            self.root,
            ["pt-PT"],
        )

        messages = [issue.message for issue in issues]
        self.assertEqual({"pt-PT": (1, 2)}, coverage)
        self.assertTrue(any("missing string translation 'missing'" in item for item in messages))
        self.assertTrue(any("changes format arguments" in item for item in messages))

    def test_locale_conversion_supports_region_and_bcp47_qualifiers(self) -> None:
        self.assertEqual("pt-rPT", localization.locale_to_qualifier("pt-PT"))
        self.assertEqual(
            "b+zh+Hant+TW",
            localization.locale_to_qualifier("zh-Hant-TW"),
        )
        self.assertEqual("pt-PT", localization.qualifier_to_locale("pt-rPT"))
        self.assertEqual(
            "zh-Hant-TW",
            localization.qualifier_to_locale("b+zh+Hant+TW"),
        )

    def test_hardcoded_compose_text_ignores_preview_only_files(self) -> None:
        source_directory = self.root / "app/src/main/kotlin/example"
        source_directory.mkdir(parents=True)
        (source_directory / "Screen.kt").write_text(
            'fun Screen() { Text("Move me") }\n',
            encoding="utf-8",
        )
        (source_directory / "ScreenPreview.kt").write_text(
            'fun Preview() { Text("Preview text") }\n',
            encoding="utf-8",
        )

        issues = localization.find_hardcoded_compose_text(self.root)

        self.assertEqual(1, len(issues))
        self.assertIn("hardcoded Compose text", issues[0].message)


if __name__ == "__main__":
    unittest.main()
