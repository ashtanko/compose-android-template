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
"""Minimal-diff editing and scaffolding for Android string resource files.

Editing an existing ``strings.xml`` touches only the target element's text, so
the license header, comments, element order, indentation, and encoding are all
preserved and the resulting git diff stays small. Scaffolding a brand new locale
generates a full file from the default catalog, reusing the module's own header.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

from .core import (
    Resource,
    ResourceId,
    canonical_locale,
    load_default_catalogs,
    locale_to_qualifier,
)


_DEFAULT_INDENT = "    "
_INDENT_PATTERN = re.compile(r"\n([ \t]+)<(?:string|plurals|string-array)\b")
_RESOURCES_OPEN = "<resources"
_RESOURCES_CLOSE = "</resources>"
_DEFAULT_HEADER = '<?xml version="1.0" encoding="utf-8"?>\n'


class WriteError(Exception):
    """A recoverable problem while editing or scaffolding a resource file."""


def escape_android_text(value: str) -> str:
    """Escape plain text for use as an Android string resource value.

    Applies XML escaping for ``&`` and ``<``, the Android backslash escapes for
    apostrophes and double quotes, and the leading ``@``/``?`` escape. Callers
    pass raw human text; the result is safe to place between resource tags.
    """

    result = value.replace("&", "&amp;").replace("<", "&lt;")
    result = result.replace("'", "\\'").replace('"', '\\"')
    if result[:1] in ("@", "?"):
        result = "\\" + result
    return result


def detect_indent(text: str) -> str:
    """Return the indentation used by resource elements, defaulting to four spaces."""

    match = _INDENT_PATTERN.search(text)
    return match.group(1) if match else _DEFAULT_INDENT


def extract_header(text: str) -> str:
    """Return everything before the opening ``<resources`` tag, verbatim."""

    index = text.find(_RESOURCES_OPEN)
    if index == -1:
        return _DEFAULT_HEADER
    return text[:index]


def has_string(text: str, name: str) -> bool:
    """Return whether a ``<string>`` with the given name already exists."""

    pattern = re.compile(
        r'<string\b[^>]*\bname="' + re.escape(name) + r'"',
    )
    return pattern.search(text) is not None


def set_string_value(text: str, name: str, value: str) -> tuple[str, bool]:
    """Replace the text of an existing ``<string>`` element in place.

    Returns the updated document and whether anything changed. Only the inner
    text of the matched element is rewritten; the tag, its attributes, and all
    surrounding formatting are left untouched.
    """

    pattern = re.compile(
        r'(<string\b[^>]*\bname="' + re.escape(name) + r'"[^>]*>)(.*?)(</string>)',
        re.S,
    )
    match = pattern.search(text)
    if match is None:
        return text, False

    escaped = escape_android_text(value)
    if match.group(2) == escaped:
        return text, False
    updated = text[: match.start(2)] + escaped + text[match.end(2) :]
    return updated, True


def add_string(
    text: str,
    name: str,
    value: str,
    translatable: bool | None = None,
) -> str:
    """Insert a new ``<string>`` element immediately before ``</resources>``."""

    if has_string(text, name):
        raise WriteError(f"string '{name}' already exists")
    close_index = text.rfind(_RESOURCES_CLOSE)
    if close_index == -1:
        raise WriteError("no </resources> element found")

    indent = detect_indent(text)
    attribute = ' translatable="false"' if translatable is False else ""
    entry = (
        f'{indent}<string name="{name}"{attribute}>'
        f"{escape_android_text(value)}</string>\n"
    )
    line_start = text.rfind("\n", 0, close_index) + 1
    return text[:line_start] + entry + text[line_start:]


def render_resource_file(
    header: str,
    resources: Mapping[ResourceId, Resource],
    fill: str = "source",
) -> str:
    """Render a complete resource file for a new locale from a default catalog.

    ``fill`` selects the placeholder for each value: ``source`` copies the
    default text as a starting point for translation, while ``empty`` leaves the
    value blank so the resource gate reports it as an outstanding translation.
    """

    lines = [header.rstrip("\n"), "<resources>"]
    for resource_id, resource in resources.items():
        lines.extend(_render_resource(resource_id, resource, fill))
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


def _fill_value(text: str, fill: str) -> str:
    return escape_android_text(text) if fill == "source" else ""


def _render_resource(
    resource_id: ResourceId,
    resource: Resource,
    fill: str,
) -> list[str]:
    """Render one resource element and its children as indented XML lines."""

    inner = _DEFAULT_INDENT + _DEFAULT_INDENT
    if resource_id.kind == "string":
        item = resource.items.get("")
        value = _fill_value(item.text if item else "", fill)
        return [f'{_DEFAULT_INDENT}<string name="{resource_id.name}">{value}</string>']
    if resource_id.kind == "plurals":
        rows = [f'{_DEFAULT_INDENT}<plurals name="{resource_id.name}">']
        for quantity, item in resource.items.items():
            rows.append(
                f'{inner}<item quantity="{quantity}">'
                f"{_fill_value(item.text, fill)}</item>",
            )
        rows.append(f"{_DEFAULT_INDENT}</plurals>")
        return rows
    rows = [f'{_DEFAULT_INDENT}<string-array name="{resource_id.name}">']
    for item in resource.items.values():
        rows.append(f"{inner}<item>{_fill_value(item.text, fill)}</item>")
    rows.append(f"{_DEFAULT_INDENT}</string-array>")
    return rows


def scaffold_locale(
    root: Path,
    locale: str,
    fill: str = "source",
    modules: list[str] | None = None,
) -> tuple[list[Path], list[Path]]:
    """Create a new locale's resource files across every owning module.

    Returns the paths created and the paths skipped because they already exist.
    Existing files are never overwritten.
    """

    resolved_root = root.resolve()
    canonical = canonical_locale(locale)
    qualifier = locale_to_qualifier(canonical)
    catalogs, _ = load_default_catalogs(resolved_root)

    created: list[Path] = []
    skipped: list[Path] = []
    for catalog in catalogs:
        if modules and catalog.module not in modules:
            continue
        translatable = {
            resource_id: resource
            for resource_id, resource in catalog.resources.items()
            if resource.translatable
        }
        if not translatable:
            continue

        target = catalog.res_root / f"values-{qualifier}" / "strings.xml"
        if target.exists():
            skipped.append(target)
            continue

        header = extract_header(_read_default_header_source(catalog.res_root))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            render_resource_file(header, translatable, fill),
            encoding="utf-8",
        )
        created.append(target)
    return created, skipped


def _read_default_header_source(res_root: Path) -> str:
    """Return the text of a default file to copy the license header from."""

    default = res_root / "values" / "strings.xml"
    if default.is_file():
        return default.read_text(encoding="utf-8")
    for candidate in sorted((res_root / "values").glob("*.xml")):
        return candidate.read_text(encoding="utf-8")
    return _DEFAULT_HEADER


def find_res_root(root: Path, module: str) -> Path:
    """Return the resource root for a module path or raise a WriteError."""

    catalogs, _ = load_default_catalogs(root.resolve())
    for catalog in catalogs:
        if catalog.module == module:
            return catalog.res_root
    known = ", ".join(catalog.module for catalog in catalogs) or "none"
    raise WriteError(f"unknown module '{module}'; known modules: {known}")


def add_default_string(
    root: Path,
    module: str,
    name: str,
    value: str,
    translatable: bool | None = None,
    file: str = "strings.xml",
) -> Path:
    """Add a new default string to a module and return the edited file path."""

    target = find_res_root(root, module) / "values" / file
    if not target.is_file():
        raise WriteError(f"{target} does not exist")
    target.write_text(
        add_string(target.read_text(encoding="utf-8"), name, value, translatable),
        encoding="utf-8",
    )
    return target


def apply_translation(
    root: Path,
    locale: str,
    module: str,
    name: str,
    value: str,
    file: str = "strings.xml",
) -> tuple[str, Path]:
    """Set one translation in place, returning the action taken and file path.

    The action is ``updated`` when an existing value changed, ``added`` when the
    key was newly inserted, or ``unchanged`` when the value already matched.
    """

    qualifier = locale_to_qualifier(canonical_locale(locale))
    target = find_res_root(root, module) / f"values-{qualifier}" / file
    if not target.is_file():
        raise WriteError(
            f"{target} does not exist; run 'add-locale {locale}' first",
        )
    text = target.read_text(encoding="utf-8")
    if has_string(text, name):
        updated, changed = set_string_value(text, name, value)
        action = "updated" if changed else "unchanged"
    else:
        updated = add_string(text, name, value)
        action = "added"
    if action != "unchanged":
        target.write_text(updated, encoding="utf-8")
    return action, target
