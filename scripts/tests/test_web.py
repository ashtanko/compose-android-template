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
"""Tests for the FastAPI web wizard backend.

These tests are skipped unless the optional web extras (FastAPI and the Starlette
test client's httpx dependency) are installed, so the dependency-free
localization gate keeps running them as clean skips.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_HAS_WEB = (
    importlib.util.find_spec("fastapi") is not None
    and importlib.util.find_spec("httpx") is not None
)

DEFAULT = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    "<resources>\n"
    '    <string name="greeting">Hello</string>\n'
    '    <string name="farewell">Goodbye</string>\n'
    "</resources>\n"
)


@unittest.skipUnless(_HAS_WEB, "FastAPI web extras are not installed")
class WebTest(unittest.TestCase):
    """Exercise the wizard API against a temporary repository."""

    def setUp(self) -> None:
        from fastapi.testclient import TestClient

        from localization.web import create_app

        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        path = self.root / "feature/a/src/main/res/values/strings.xml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT, encoding="utf-8")
        self.client = TestClient(create_app(self.root))

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_catalog_lists_modules(self) -> None:
        payload = self.client.get("/api/catalog").json()
        self.assertEqual(["feature/a"], payload["modules"])
        self.assertEqual([], payload["locales"])

    def test_scaffold_then_edit_updates_coverage(self) -> None:
        created = self.client.post(
            "/api/locales",
            json={"locale": "pt-PT", "fill": "empty"},
        )
        self.assertEqual(200, created.status_code)
        self.assertEqual(1, len(created.json()["created"]))

        edit = self.client.post(
            "/api/translation",
            json={
                "locale": "pt-PT",
                "module": "feature/a",
                "name": "greeting",
                "text": "Ola",
            },
        )
        # Empty-fill scaffolding already contains the key, so this is an update.
        self.assertEqual("updated", edit.json()["action"])

        catalog = self.client.get("/api/catalog").json()
        self.assertEqual(1, catalog["locales"][0]["translated"])
        self.assertEqual(2, catalog["locales"][0]["total"])

    def test_unknown_module_returns_400(self) -> None:
        self.client.post("/api/locales", json={"locale": "pt-PT", "fill": "empty"})
        response = self.client.post(
            "/api/translation",
            json={
                "locale": "pt-PT",
                "module": "missing",
                "name": "greeting",
                "text": "x",
            },
        )
        self.assertEqual(400, response.status_code)


if __name__ == "__main__":
    unittest.main()
