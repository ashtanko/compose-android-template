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
"""Tests for CSV and XLIFF export and import round-trips."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from localization import (  # noqa: E402
    build_report,
    check_repository,
    export_xliff,
    import_translations,
    resolve_format,
    scaffold_locale,
)


DEFAULT = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    "<resources>\n"
    '    <string name="greeting">Hello</string>\n'
    '    <string name="farewell">Goodbye &amp; take care</string>\n'
    "</resources>\n"
)


class ExchangeTest(unittest.TestCase):
    """Exercise XLIFF export and CSV/XLIFF import into module files."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        path = self.root / "feature/a/src/main/res/values/strings.xml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT, encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_resolve_format_from_suffix(self) -> None:
        self.assertEqual("csv", resolve_format(Path("a.csv"), "auto"))
        self.assertEqual("xliff", resolve_format(Path("a.xlf"), "auto"))
        self.assertEqual("csv", resolve_format(Path("a.xlf"), "csv"))
        with self.assertRaises(ValueError):
            resolve_format(Path("a.txt"), "auto")

    def test_export_xliff_is_valid_and_encodes_ids(self) -> None:
        scaffold_locale(self.root, "pt-PT", fill="source")
        document, issues = export_xliff(self.root, "pt-PT")

        self.assertEqual([], issues)
        root = ElementTree.fromstring(document)
        ids = [unit.get("id") for unit in root.iter() if unit.tag.endswith("trans-unit")]
        self.assertIn("feature/a|string|greeting|", ids)

    def test_csv_import_fills_locale_and_passes_check(self) -> None:
        scaffold_locale(self.root, "pt-PT", fill="empty")
        csv_path = self.root / "in.csv"
        csv_path.write_text(
            "module,resource_type,key,item,translation\n"
            "feature/a,string,greeting,,Ola\n"
            'feature/a,string,farewell,,Adeus & fica bem\n',
            encoding="utf-8",
        )

        summary = import_translations(self.root, "pt-PT", csv_path)

        self.assertEqual(2, summary.applied)
        issues, coverage = check_repository(self.root, ["pt-PT"])
        self.assertEqual([], issues)
        self.assertEqual((2, 2), coverage["pt-PT"])
        # The ampersand is XML-escaped when written back.
        target = self.root / "feature/a/src/main/res/values-pt-rPT/strings.xml"
        self.assertIn("Adeus &amp; fica bem", target.read_text(encoding="utf-8"))

    def test_import_is_idempotent(self) -> None:
        scaffold_locale(self.root, "pt-PT", fill="source")
        rows, _ = build_report(self.root, "pt-PT")
        # Round-trip the current translations back in; nothing should change.
        document, _ = export_xliff(self.root, "pt-PT")
        xliff_path = self.root / "out.xlf"
        xliff_path.write_text(document, encoding="utf-8")

        summary = import_translations(self.root, "pt-PT", xliff_path)

        self.assertEqual(0, summary.applied)
        self.assertEqual(len(rows), summary.unchanged)

    def test_non_string_units_are_reported_unsupported(self) -> None:
        scaffold_locale(self.root, "pt-PT", fill="empty")
        csv_path = self.root / "in.csv"
        csv_path.write_text(
            "module,resource_type,key,item,translation\n"
            "feature/a,plurals,count,other,Muitos\n",
            encoding="utf-8",
        )

        summary = import_translations(self.root, "pt-PT", csv_path)

        self.assertEqual(0, summary.applied)
        self.assertEqual(1, len(summary.unsupported))


if __name__ == "__main__":
    unittest.main()
