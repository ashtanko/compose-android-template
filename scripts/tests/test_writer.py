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
"""Tests for the minimal-diff resource writer and locale scaffolding."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from localization import (  # noqa: E402
    WriteError,
    add_default_string,
    add_string,
    apply_translation,
    check_repository,
    escape_android_text,
    has_string,
    scaffold_locale,
    set_string_value,
)


HEADER = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    "<!-- Licensed under the Apache License, Version 2.0 -->\n"
)
DEFAULT = (
    f"{HEADER}"
    "<resources>\n"
    '    <string name="app_name" translatable="false">Sample</string>\n'
    '    <string name="greeting">Hello</string>\n'
    "</resources>\n"
)


class WriterTest(unittest.TestCase):
    """Exercise escaping, in-place edits, insertion, and scaffolding."""

    def test_escape_android_text(self) -> None:
        self.assertEqual("Tom &amp; Jerry", escape_android_text("Tom & Jerry"))
        self.assertEqual("a &lt; b", escape_android_text("a < b"))
        self.assertEqual("It\\'s", escape_android_text("It's"))
        self.assertEqual('\\"quoted\\"', escape_android_text('"quoted"'))
        self.assertEqual("\\@handle", escape_android_text("@handle"))

    def test_set_string_value_is_minimal(self) -> None:
        updated, changed = set_string_value(DEFAULT, "greeting", "Hi there")

        self.assertTrue(changed)
        # Only the greeting line changes; every other line is untouched.
        before = DEFAULT.splitlines()
        after = updated.splitlines()
        self.assertEqual(len(before), len(after))
        differing = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertEqual(1, len(differing))
        self.assertIn(">Hi there<", after[differing[0]])
        self.assertIn("app_name", updated)
        self.assertIn("Apache License", updated)

    def test_set_string_value_escapes_and_detects_no_change(self) -> None:
        updated, changed = set_string_value(DEFAULT, "greeting", "Tom & Jerry")
        self.assertTrue(changed)
        self.assertIn(">Tom &amp; Jerry<", updated)

        again, changed_again = set_string_value(updated, "greeting", "Tom & Jerry")
        self.assertFalse(changed_again)
        self.assertEqual(updated, again)

    def test_set_string_value_missing_key_is_noop(self) -> None:
        updated, changed = set_string_value(DEFAULT, "absent", "x")
        self.assertFalse(changed)
        self.assertEqual(DEFAULT, updated)

    def test_add_string_inserts_before_close_with_indent(self) -> None:
        updated = add_string(DEFAULT, "farewell", "Goodbye")

        self.assertIn('    <string name="farewell">Goodbye</string>\n', updated)
        self.assertLess(updated.index("farewell"), updated.index("</resources>"))
        self.assertTrue(has_string(updated, "farewell"))

    def test_add_string_rejects_duplicate(self) -> None:
        with self.assertRaises(WriteError):
            add_string(DEFAULT, "greeting", "Hi")

    def test_add_string_can_mark_not_translatable(self) -> None:
        updated = add_string(DEFAULT, "brand", "Acme", translatable=False)
        self.assertIn('<string name="brand" translatable="false">Acme</string>', updated)


class ScaffoldTest(unittest.TestCase):
    """Exercise new-locale scaffolding across modules."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self._write("feature/a/src/main/res/values/strings.xml", DEFAULT)
        self._write(
            "feature/b/src/main/res/values/strings.xml",
            f'{HEADER}<resources>\n'
            '    <string name="title">Posts</string>\n'
            "</resources>\n",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_scaffold_creates_files_reusing_header(self) -> None:
        created, skipped = scaffold_locale(self.root, "pt-PT", fill="source")

        self.assertEqual([], skipped)
        self.assertEqual(2, len(created))
        target = self.root / "feature/a/src/main/res/values-pt-rPT/strings.xml"
        self.assertIn(target, created)
        content = target.read_text(encoding="utf-8")
        self.assertIn("Apache License", content)
        self.assertIn('<string name="greeting">Hello</string>', content)
        # translatable="false" resources are not scaffolded for translation.
        self.assertNotIn("app_name", content)

    def test_scaffold_empty_fill_reports_missing_via_check(self) -> None:
        scaffold_locale(self.root, "pt-PT", fill="empty")

        issues, _ = check_repository(self.root, ["pt-PT"])
        messages = [issue.message for issue in issues]
        self.assertTrue(any("empty translation" in message for message in messages))

    def test_scaffold_source_fill_passes_check(self) -> None:
        scaffold_locale(self.root, "pt-PT", fill="source")

        issues, coverage = check_repository(self.root, ["pt-PT"])
        self.assertEqual([], issues)
        self.assertEqual((2, 2), coverage["pt-PT"])

    def test_scaffold_skips_existing_and_respects_module_filter(self) -> None:
        created, _ = scaffold_locale(
            self.root,
            "pt-PT",
            modules=["feature/a"],
        )
        self.assertEqual(1, len(created))

        created_again, skipped = scaffold_locale(self.root, "pt-PT")
        self.assertEqual(
            {(self.root / "feature/a/src/main/res/values-pt-rPT/strings.xml")},
            set(skipped),
        )
        self.assertEqual(1, len(created_again))


class ServiceTest(unittest.TestCase):
    """Exercise the module-aware write services shared by the CLI and web API."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        path = self.root / "feature/a/src/main/res/values/strings.xml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT, encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_apply_translation_actions(self) -> None:
        # Empty-fill scaffolding already contains the key, so the first set of an
        # existing (empty) value is an update, and re-setting it is a no-op.
        scaffold_locale(self.root, "pt-PT", fill="empty")

        action, target = apply_translation(
            self.root, "pt-PT", "feature/a", "greeting", "Ola",
        )
        self.assertEqual("updated", action)
        self.assertIn(">Ola<", target.read_text(encoding="utf-8"))

        action, _ = apply_translation(
            self.root, "pt-PT", "feature/a", "greeting", "Ola",
        )
        self.assertEqual("unchanged", action)

        # A key absent from the locale file is inserted.
        action, _ = apply_translation(
            self.root, "pt-PT", "feature/a", "brand_new", "Nova",
        )
        self.assertEqual("added", action)

    def test_apply_translation_requires_locale_file(self) -> None:
        with self.assertRaises(WriteError):
            apply_translation(self.root, "pt-PT", "feature/a", "greeting", "x")

    def test_apply_translation_unknown_module(self) -> None:
        scaffold_locale(self.root, "pt-PT", fill="empty")
        with self.assertRaises(WriteError):
            apply_translation(self.root, "pt-PT", "feature/z", "greeting", "x")

    def test_add_default_string_service(self) -> None:
        target = add_default_string(self.root, "feature/a", "welcome", "Welcome")
        self.assertIn(
            '<string name="welcome">Welcome</string>',
            target.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
