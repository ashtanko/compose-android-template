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
"""Tests for the non-fatal localization quality warnings."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from localization import collect_warnings  # noqa: E402


class WarningsTest(unittest.TestCase):
    """Exercise truncation, untranslated, and drift warnings."""

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

    def categories(self, key: str) -> set[str]:
        warnings = collect_warnings(self.root)
        return {w.category for w in warnings if f"'{key}'" in w.message}

    def test_format_only_identical_value_is_not_untranslated(self) -> None:
        self.write_resources(
            "values",
            '<string name="equation">%1$d! = %2$d</string>',
        )
        self.write_resources(
            "values-pt-rPT",
            '<string name="equation">%1$d! = %2$d</string>',
        )

        self.assertNotIn("untranslated", self.categories("equation"))

    def test_identical_phrase_is_flagged_as_untranslated(self) -> None:
        self.write_resources(
            "values",
            '<string name="welcome_message">Welcome back home</string>',
        )
        self.write_resources(
            "values-pt-rPT",
            '<string name="welcome_message">Welcome back home</string>',
        )

        self.assertIn("untranslated", self.categories("welcome_message"))

    def test_much_longer_translation_is_flagged_as_length(self) -> None:
        self.write_resources(
            "values",
            '<string name="empty_state">No posts yet</string>',
        )
        self.write_resources(
            "values-pt-rPT",
            '<string name="empty_state">Ainda nao ha publicacoes disponiveis</string>',
        )

        self.assertIn("length", self.categories("empty_state"))

    def test_line_break_drift_is_flagged(self) -> None:
        self.write_resources(
            "values",
            r'<string name="two_lines">First line\nSecond line</string>',
        )
        self.write_resources(
            "values-pt-rPT",
            r'<string name="two_lines">Primeira linha Segunda linha</string>',
        )

        self.assertIn("line-break", self.categories("two_lines"))

    def test_clean_translation_produces_no_warnings(self) -> None:
        self.write_resources(
            "values",
            '<string name="greeting">Hello there</string>',
        )
        self.write_resources(
            "values-pt-rPT",
            '<string name="greeting">Ola pessoal</string>',
        )

        self.assertEqual(set(), self.categories("greeting"))


if __name__ == "__main__":
    unittest.main()
