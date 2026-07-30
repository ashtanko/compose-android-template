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
"""Detect default text resources that are never referenced from source.

References are collected from ``R.string`` / ``R.plurals`` / ``R.array`` lookups
in Kotlin and from ``@string`` / ``@plurals`` / ``@array`` references in XML
(layouts, themes, the manifest). Detection is advisory only: a resource loaded
dynamically by name cannot be seen here, so orphans are reported for review and
never deleted automatically.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .core import (
    IGNORED_DIRECTORY_NAMES,
    ResourceId,
    load_default_catalogs,
)


# Android reference syntax uses "array" for the "string-array" resource kind.
_REFERENCE_KIND = {
    "string": "string",
    "plurals": "plurals",
    "string-array": "array",
}
_R_REFERENCE = re.compile(r"\bR\.(string|plurals|array)\.(\w+)")
_AT_REFERENCE = re.compile(r"@(?:\w+:)?(string|plurals|array)/(\w+)")
_SCANNED_SUFFIXES = {".kt", ".java", ".xml"}


@dataclass(frozen=True)
class Orphan:
    """A default resource with no discovered reference in source."""

    module: str
    resource_id: ResourceId
    source: Path


def collect_references(root: Path) -> set[tuple[str, str]]:
    """Return every ``(kind, name)`` resource reference found under ``src/main``."""

    references: set[tuple[str, str]] = set()
    for directory, child_names, file_names in os.walk(root):
        child_names[:] = sorted(
            name for name in child_names if name not in IGNORED_DIRECTORY_NAMES
        )
        path = Path(directory)
        path_parts = path.relative_to(root).parts
        if not any(
            path_parts[index : index + 2] == ("src", "main")
            for index in range(len(path_parts) - 1)
        ):
            continue

        for file_name in sorted(file_names):
            source = path / file_name
            if source.suffix not in _SCANNED_SUFFIXES:
                continue
            try:
                text = source.read_text(encoding="utf-8")
            except OSError:
                continue
            for pattern in (_R_REFERENCE, _AT_REFERENCE):
                for match in pattern.finditer(text):
                    references.add((match.group(1), match.group(2)))
    return references


def find_orphans(root: Path) -> list[Orphan]:
    """Return default resources that no scanned source file references."""

    resolved_root = root.resolve()
    catalogs, _ = load_default_catalogs(resolved_root)
    references = collect_references(resolved_root)

    orphans: list[Orphan] = []
    for catalog in catalogs:
        for resource_id, resource in sorted(catalog.resources.items()):
            reference_kind = _REFERENCE_KIND[resource_id.kind]
            if (reference_kind, resource_id.name) not in references:
                orphans.append(
                    Orphan(
                        module=catalog.module,
                        resource_id=resource_id,
                        source=resource.source,
                    ),
                )
    return orphans
