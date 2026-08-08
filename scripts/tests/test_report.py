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
"""Tests for the HTML localization report generator."""

from __future__ import annotations

import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from localization import build_model, render_html, write_html_report  # noqa: E402


class _BalanceChecker(HTMLParser):
    """Verify that non-void elements are opened and closed in balance."""

    VOID = {"meta", "br", "input", "img", "hr"}

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.balanced = True

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass
        else:
            self.balanced = False


class ReportTest(unittest.TestCase):
    """Exercise report aggregation and HTML rendering."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_resources(self, qualifier: str, body: str) -> None:
        directory = self.root / "feature/example/src/main/res" / qualifier
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "strings.xml").write_text(
            f'<?xml version="1.0" encoding="utf-8"?>\n'
            f"<resources>{body}</resources>\n",
            encoding="utf-8",
        )

    def seed(self) -> None:
        self.write_resources(
            "values",
            """
            <string name="greeting">Hello</string>
            <string name="farewell">Goodbye</string>
            """,
        )
        self.write_resources(
            "values-pt-rPT",
            '<string name="greeting">Ola</string>',
        )

    def test_model_reports_partial_coverage(self) -> None:
        self.seed()

        model = build_model(self.root)

        self.assertEqual(["pt-PT"], [locale.locale for locale in model.locales])
        summary = model.locales[0]
        self.assertEqual(1, summary.translated)
        self.assertEqual(2, summary.total)
        self.assertEqual(50.0, summary.percent)
        self.assertTrue(any("farewell" in error for error in model.errors))

    def test_render_html_is_balanced_and_escaped(self) -> None:
        self.write_resources(
            "values",
            '<string name="danger">Tom &amp; Jerry &lt;b&gt;</string>',
        )
        self.write_resources(
            "values-pt-rPT",
            '<string name="danger">Tom &amp; Jerry &lt;b&gt;</string>',
        )

        document = render_html(build_model(self.root))

        checker = _BalanceChecker()
        checker.feed(document)
        self.assertTrue(checker.balanced)
        self.assertEqual([], checker.stack)
        self.assertIn("Tom &amp; Jerry &lt;b&gt;", document)
        self.assertNotIn("<b>", document)

    def test_write_html_report_creates_file(self) -> None:
        self.seed()
        output = self.root / "out" / "index.html"

        model = write_html_report(self.root, output)

        self.assertTrue(output.is_file())
        self.assertIn("Localization status", output.read_text(encoding="utf-8"))
        self.assertEqual(1, model.translated)


if __name__ == "__main__":
    unittest.main()
