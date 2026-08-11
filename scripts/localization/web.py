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
"""FastAPI backend for the local localization wizard.

This module is a development-only tool. It is never packaged into the app and is
intentionally excluded from the ``localization`` package's public exports so the
dependency-free localization gate never imports FastAPI. It exposes a small JSON
API over the same core the command line uses, so every read and every edit goes
through one validated, tested code path.
"""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .core import build_report
from .orphans import find_orphans
from .report import build_model
from .warnings import collect_warnings
from .writer import (
    WriteError,
    add_default_string,
    apply_translation,
    scaffold_locale,
)


class TranslationUpdate(BaseModel):
    """Request body for setting a single translation value."""

    locale: str
    module: str
    name: str
    text: str
    file: str = "strings.xml"


class NewLocale(BaseModel):
    """Request body for scaffolding a new locale."""

    locale: str
    fill: str = "source"
    modules: list[str] | None = None


class NewString(BaseModel):
    """Request body for adding a new default string."""

    module: str
    name: str
    text: str
    translatable: bool | None = None
    file: str = "strings.xml"


def _catalog_payload(root: Path) -> dict:
    model = build_model(root)
    return {
        "generated_at": model.generated_at,
        "modules": model.modules,
        "locales": [
            {
                "tag": locale.locale,
                "translated": locale.translated,
                "total": locale.total,
                "percent": round(locale.percent, 1),
                "warnings": len(locale.warnings),
            }
            for locale in model.locales
        ],
        "errors": model.errors,
        "orphans": [
            {
                "module": orphan.module,
                "kind": orphan.resource_id.kind,
                "name": orphan.resource_id.name,
            }
            for orphan in model.orphans
        ],
    }


def _locale_payload(root: Path, tag: str) -> dict:
    rows, issues = build_report(root, tag)
    if issues:
        raise HTTPException(
            status_code=409,
            detail=[issue.message for issue in issues],
        )
    warnings = collect_warnings(root, [tag])
    return {
        "tag": tag,
        "translated": sum(row.status == "translated" for row in rows),
        "total": len(rows),
        "rows": [dataclasses.asdict(row) for row in rows],
        "warnings": [
            {
                "module": warning.module,
                "category": warning.category,
                "message": warning.message,
            }
            for warning in warnings
        ],
    }


def create_app(root: Path | None = None) -> FastAPI:
    """Create the wizard application bound to a repository root."""

    repo_root = (root or Path(os.environ.get("LOCALIZATION_ROOT", "."))).resolve()
    app = FastAPI(title="Localization wizard", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/catalog")
    def get_catalog() -> dict:
        return _catalog_payload(repo_root)

    @app.get("/api/locales/{tag}")
    def get_locale(tag: str) -> dict:
        return _locale_payload(repo_root, tag)

    @app.post("/api/locales")
    def post_locale(body: NewLocale) -> dict:
        try:
            created, skipped = scaffold_locale(
                repo_root,
                body.locale,
                body.fill,
                body.modules,
            )
        except (WriteError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {
            "created": [str(path.relative_to(repo_root)) for path in created],
            "skipped": [str(path.relative_to(repo_root)) for path in skipped],
        }

    @app.post("/api/translation")
    def post_translation(body: TranslationUpdate) -> dict:
        try:
            action, target = apply_translation(
                repo_root,
                body.locale,
                body.module,
                body.name,
                body.text,
                body.file,
            )
        except (WriteError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"action": action, "file": str(target.relative_to(repo_root))}

    @app.post("/api/strings")
    def post_string(body: NewString) -> dict:
        try:
            target = add_default_string(
                repo_root,
                body.module,
                body.name,
                body.text,
                body.translatable,
                body.file,
            )
        except (WriteError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"file": str(target.relative_to(repo_root))}

    @app.get("/api/orphans")
    def get_orphans() -> list[dict]:
        return [
            {
                "module": orphan.module,
                "kind": orphan.resource_id.kind,
                "name": orphan.resource_id.name,
            }
            for orphan in find_orphans(repo_root)
        ]

    _mount_frontend(app)
    return app


def _mount_frontend(app: FastAPI) -> None:
    """Serve the built React frontend at the root when it has been built."""

    dist = Path(__file__).resolve().parents[2] / "tools" / "localization-web" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")


app = create_app()
