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
"""Non-fatal localization quality warnings.

Warnings sit one severity below the errors produced by :mod:`localization.core`.
They surface likely quality problems (truncation risk, forgotten translations,
line-break drift, and trailing-punctuation drift) without failing the fast
localization gate. Every check operates on the parsed resource model, so a
warning never depends on how the underlying XML happens to be formatted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .core import (
    FORMAT_ARGUMENT_PATTERN,
    ModuleCatalog,
    ResourceId,
    ResourceItem,
    canonical_locale,
    discover_locales,
    load_default_catalogs,
    locale_to_qualifier,
    parse_resource_directory,
)


# A translation this many times longer than its source risks clipping in fixed
# layouts; one this much shorter is often an unfinished or truncated value.
LENGTH_RATIO_HIGH = 1.8
LENGTH_RATIO_LOW = 0.4
# Ratio checks ignore very short source text, where a single extra word already
# produces a large ratio without signalling a real layout problem.
LENGTH_RATIO_MIN_SOURCE = 12
# A literal newline escape in an Android string, counted as authored in XML.
LINE_BREAK = "\\n"
TRAILING_PUNCTUATION = ("…", ":")
# A run of two or more letters, i.e. a real word rather than a stray initial.
_WORD = re.compile(r"[^\W\d_]{2,}", re.UNICODE)


@dataclass(frozen=True)
class LintWarning:
    """A non-fatal localization quality finding."""

    path: Path
    locale: str
    module: str
    category: str
    message: str


def _looks_translatable_phrase(text: str) -> bool:
    """Return whether text carries real words once format specifiers are removed.

    Format-only or symbolic values such as ``%1$d! = %2$d`` are legitimately
    identical across locales, so they must not be reported as untranslated.
    """

    without_arguments = FORMAT_ARGUMENT_PATTERN.sub(" ", text)
    return len(_WORD.findall(without_arguments)) >= 2


def compare_item_warnings(
    base_item: ResourceItem,
    translated_item: ResourceItem,
    resource_id: ResourceId,
    item: str,
    locale: str,
    module: str,
) -> list[LintWarning]:
    """Return quality warnings for one translated leaf value."""

    warnings: list[LintWarning] = []
    source = base_item.text
    target = translated_item.text
    if not source or not target:
        return warnings

    def add(category: str, message: str) -> None:
        warnings.append(
            LintWarning(
                path=translated_item.source,
                locale=locale,
                module=module,
                category=category,
                message=(
                    f"{resource_id.kind} '{resource_id.name}'"
                    f"{item_label_for(resource_id, item)} {message}"
                ),
            ),
        )

    if source == target and _looks_translatable_phrase(source):
        add("untranslated", "is identical to the source text")

    if len(source) >= LENGTH_RATIO_MIN_SOURCE:
        ratio = len(target) / len(source)
        if ratio >= LENGTH_RATIO_HIGH:
            add(
                "length",
                f"is {ratio:.1f}x longer than the source and may be truncated",
            )
        elif ratio <= LENGTH_RATIO_LOW:
            add(
                "length",
                f"is {ratio:.1f}x the source length and may be incomplete",
            )

    if source.count(LINE_BREAK) != target.count(LINE_BREAK):
        add(
            "line-break",
            (
                f"has {target.count(LINE_BREAK)} line breaks but the source has "
                f"{source.count(LINE_BREAK)}"
            ),
        )

    for mark in TRAILING_PUNCTUATION:
        if source.endswith(mark) != target.endswith(mark):
            add(
                "punctuation",
                f"differs from the source in trailing '{mark}'",
            )

    return warnings


def item_label_for(resource_id: ResourceId, item: str) -> str:
    """Format an optional plural quantity or array index without a Resource."""

    if resource_id.kind == "plurals":
        return f" quantity '{item}'"
    if resource_id.kind == "string-array":
        return f" item {item}"
    return ""


def collect_warnings(
    root: Path,
    requested_locales: Sequence[str] | None = None,
) -> list[LintWarning]:
    """Collect quality warnings for every translated value in each locale."""

    resolved_root = root.resolve()
    catalogs, _ = load_default_catalogs(resolved_root)
    if not catalogs:
        return []

    if requested_locales:
        locales = sorted({canonical_locale(locale) for locale in requested_locales})
    else:
        locales = discover_locales(catalogs)

    warnings: list[LintWarning] = []
    for locale in locales:
        warnings.extend(_collect_locale_warnings(catalogs, locale))
    return warnings


def _collect_locale_warnings(
    catalogs: Sequence[ModuleCatalog],
    locale: str,
) -> list[LintWarning]:
    """Collect warnings for one locale across every module."""

    warnings: list[LintWarning] = []
    qualifier = locale_to_qualifier(locale)
    for catalog in catalogs:
        translations, _ = parse_resource_directory(
            catalog.res_root / f"values-{qualifier}",
            locale,
        )
        for resource_id, base in sorted(catalog.resources.items()):
            if not base.translatable:
                continue
            translation = translations.get(resource_id)
            if translation is None:
                continue
            for item, base_item in sorted(base.items.items()):
                translated_item = translation.items.get(item)
                if translated_item is None:
                    continue
                warnings.extend(
                    compare_item_warnings(
                        base_item,
                        translated_item,
                        resource_id,
                        item,
                        locale,
                        catalog.module,
                    ),
                )
    return warnings
