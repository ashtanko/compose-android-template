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
"""Exchange translations with a translation-management system.

Export a locale to XLIFF 1.2 for a translator, and import a filled CSV or XLIFF
file back into the module resource files through the minimal-diff writer. The
report command already exports CSV and JSON; the same CSV columns are accepted on
import. String resources round-trip fully; plural and array units are reported as
unsupported rather than written incorrectly.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence
from xml.etree import ElementTree
from xml.sax.saxutils import escape, quoteattr

from .core import (
    ReportRow,
    build_report,
    canonical_locale,
    load_default_catalogs,
    local_name,
    locale_to_qualifier,
)
from .writer import add_string, extract_header, has_string, set_string_value


_ID_SEPARATOR = "|"
_XLIFF_NAMESPACE = "urn:oasis:names:tc:xliff:document:1.2"


@dataclass
class ImportSummary:
    """The outcome of importing translations into the repository."""

    applied: int = 0
    unchanged: int = 0
    skipped_empty: int = 0
    unsupported: list[str] = field(default_factory=list)
    written_files: list[Path] = field(default_factory=list)


@dataclass(frozen=True)
class _Entry:
    """One incoming translation unit from a CSV or XLIFF file."""

    module: str
    kind: str
    key: str
    item: str
    translation: str


def render_xliff(rows: Sequence[ReportRow], locale: str) -> str:
    """Render report rows as an XLIFF 1.2 document grouped by module."""

    canonical = canonical_locale(locale)
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<xliff version="1.2" xmlns="{_XLIFF_NAMESPACE}">',
    ]
    for module in sorted({row.module for row in rows}):
        lines.append(
            f"  <file original={quoteattr(module)} source-language=\"en\" "
            f"target-language={quoteattr(canonical)} datatype=\"plaintext\">",
        )
        lines.append("    <body>")
        for row in [row for row in rows if row.module == module]:
            unit_id = _ID_SEPARATOR.join(
                (row.module, row.resource_type, row.key, row.item),
            )
            state = "translated" if row.status == "translated" else "needs-translation"
            lines.append(f"      <trans-unit id={quoteattr(unit_id)}>")
            lines.append(f"        <source>{escape(row.source_text)}</source>")
            lines.append(
                f'        <target state="{state}">{escape(row.translation)}</target>',
            )
            lines.append("      </trans-unit>")
        lines.append("    </body>")
        lines.append("  </file>")
    lines.append("</xliff>")
    return "\n".join(lines) + "\n"


def export_xliff(root: Path, locale: str) -> tuple[str, list]:
    """Build the XLIFF document for one locale, returning it with any issues."""

    rows, issues = build_report(root, locale)
    return render_xliff(rows, locale), issues


def resolve_format(path: Path, requested: str) -> str:
    """Resolve the import format from an explicit choice or the file suffix."""

    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".xlf", ".xliff", ".xml"}:
        return "xliff"
    raise ValueError(f"cannot infer format from '{path.name}'; pass --format")


def _read_csv_entries(text: str) -> list[_Entry]:
    reader = csv.DictReader(io.StringIO(text))
    required = {"module", "resource_type", "key", "item", "translation"}
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
    return [
        _Entry(
            module=row["module"],
            kind=row["resource_type"],
            key=row["key"],
            item=row["item"] or "",
            translation=row["translation"] or "",
        )
        for row in reader
    ]


def _read_xliff_entries(text: str) -> list[_Entry]:
    root = ElementTree.fromstring(text)
    entries: list[_Entry] = []
    for unit in root.iter():
        if local_name(unit.tag) != "trans-unit":
            continue
        unit_id = unit.get("id", "")
        parts = unit_id.split(_ID_SEPARATOR)
        if len(parts) != 4:
            continue
        module, kind, key, item = parts
        target = ""
        for child in unit:
            if local_name(child.tag) == "target":
                target = "".join(child.itertext())
                break
        entries.append(_Entry(module, kind, key, item, target))
    return entries


def _read_entries(source: Path, output_format: str) -> list[_Entry]:
    text = source.read_text(encoding="utf-8")
    if output_format == "csv":
        return _read_csv_entries(text)
    return _read_xliff_entries(text)


def import_translations(
    root: Path,
    locale: str,
    source: Path,
    output_format: str = "auto",
) -> ImportSummary:
    """Import a CSV or XLIFF file's translations for one locale into the repo."""

    resolved_root = root.resolve()
    qualifier = locale_to_qualifier(canonical_locale(locale))
    resolved_format = resolve_format(source, output_format)
    entries = _read_entries(source, resolved_format)

    catalogs, _ = load_default_catalogs(resolved_root)
    res_root_by_module = {catalog.module: catalog.res_root for catalog in catalogs}

    summary = ImportSummary()
    file_texts: dict[Path, str] = {}
    for entry in entries:
        if entry.kind != "string" or entry.item not in ("", None):
            summary.unsupported.append(
                f"{entry.module}:{entry.kind}/{entry.key} (only <string> is supported)",
            )
            continue
        if not entry.translation:
            summary.skipped_empty += 1
            continue
        res_root = res_root_by_module.get(entry.module)
        if res_root is None:
            summary.unsupported.append(f"{entry.module} (unknown module)")
            continue

        target = res_root / f"values-{qualifier}" / "strings.xml"
        text = file_texts.get(target)
        if text is None:
            text = (
                target.read_text(encoding="utf-8")
                if target.is_file()
                else _empty_locale_file(res_root)
            )
        if has_string(text, entry.key):
            text, changed = set_string_value(text, entry.key, entry.translation)
            if changed:
                summary.applied += 1
            else:
                summary.unchanged += 1
        else:
            text = add_string(text, entry.key, entry.translation)
            summary.applied += 1
        file_texts[target] = text

    for target, text in file_texts.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        summary.written_files.append(target)
    return summary


def _empty_locale_file(res_root: Path) -> str:
    """Return an empty locale file skeleton reusing the module's header."""

    default = res_root / "values" / "strings.xml"
    header = extract_header(
        default.read_text(encoding="utf-8") if default.is_file() else "",
    )
    return header.rstrip("\n") + "\n<resources>\n</resources>\n"
