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
"""Check Android translations and export translator-friendly locale reports."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence, TextIO
from xml.etree import ElementTree


IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".gradle",
    ".idea",
    ".kotlin",
    "build",
}
SUPPORTED_RESOURCE_TYPES = {
    "plurals",
    "string",
    "string-array",
}
SIMPLE_LOCALE_PATTERN = re.compile(
    r"^(?P<language>[a-z]{2,3})(?:-r(?P<region>[A-Z]{2}|\d{3}))?$",
)
FORMAT_ARGUMENT_PATTERN = re.compile(
    r"%(?:(?P<index>\d+)\$)?"
    r"(?P<flags>[-#+ 0,(<]*)"
    r"(?:\d+)?"
    r"(?:\.\d+)?"
    r"(?:(?P<date_prefix>[tT])(?P<date_conversion>[A-Za-z])"
    r"|(?P<conversion>[A-Za-z%]))",
)
HARD_CODED_COMPOSE_TEXT_PATTERN = re.compile(
    r'\bText\s*\(\s*(?:text\s*=\s*)?"[^"]+"'
    r'|contentDescription\s*=\s*"[^"]+"',
)


@dataclass(frozen=True, order=True)
class ResourceId:
    """The stable identity of one Android text resource."""

    kind: str
    name: str


@dataclass(frozen=True)
class ResourceItem:
    """One string, plural quantity, or array item."""

    text: str
    source: Path


@dataclass(frozen=True)
class Resource:
    """A localizable Android resource and its child values."""

    resource_id: ResourceId
    items: dict[str, ResourceItem]
    source: Path
    translatable: bool


@dataclass(frozen=True)
class ModuleCatalog:
    """Default resources for one Android module."""

    module: str
    res_root: Path
    resources: dict[ResourceId, Resource]


@dataclass(frozen=True)
class Issue:
    """An actionable localization validation failure."""

    path: Path
    locale: str
    message: str


@dataclass(frozen=True)
class ReportRow:
    """A leaf translation row suitable for text, JSON, or CSV output."""

    locale: str
    module: str
    resource_type: str
    key: str
    item: str
    source_text: str
    translation: str
    status: str
    source_file: str
    translation_file: str


def local_name(tag: str) -> str:
    """Remove an optional XML namespace from a tag."""

    return tag.rsplit("}", maxsplit=1)[-1]


def canonical_locale(locale: str) -> str:
    """Normalize a BCP 47 locale tag used by the command line."""

    parts = locale.replace("_", "-").split("-")
    if not parts or not re.fullmatch(r"[A-Za-z]{2,3}", parts[0]):
        raise ValueError(f"invalid locale tag: {locale}")

    normalized = [parts[0].lower()]
    for part in parts[1:]:
        if re.fullmatch(r"[A-Za-z]{4}", part):
            normalized.append(part.title())
        elif re.fullmatch(r"[A-Za-z]{2}|\d{3}", part):
            normalized.append(part.upper())
        elif re.fullmatch(r"[A-Za-z0-9]{4,8}", part):
            normalized.append(part.lower())
        else:
            raise ValueError(f"invalid locale tag: {locale}")
    return "-".join(normalized)


def locale_to_qualifier(locale: str) -> str:
    """Convert a BCP 47 tag to an Android values directory qualifier."""

    canonical = canonical_locale(locale)
    parts = canonical.split("-")
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2 and re.fullmatch(r"[A-Z]{2}|\d{3}", parts[1]):
        return f"{parts[0]}-r{parts[1]}"
    return "b+" + "+".join(parts)


def qualifier_to_locale(qualifier: str) -> str | None:
    """Convert a locale-only Android values qualifier to a BCP 47 tag."""

    simple_match = SIMPLE_LOCALE_PATTERN.fullmatch(qualifier)
    if simple_match:
        language = simple_match.group("language")
        region = simple_match.group("region")
        return canonical_locale(f"{language}-{region}" if region else language)
    if qualifier.startswith("b+"):
        try:
            return canonical_locale(qualifier.removeprefix("b+").replace("+", "-"))
        except ValueError:
            return None
    return None


def discover_res_roots(root: Path) -> list[Path]:
    """Find source-controlled Android main resource roots without scanning outputs."""

    result: list[Path] = []
    for directory, child_names, _ in os.walk(root):
        child_names[:] = sorted(
            name for name in child_names if name not in IGNORED_DIRECTORY_NAMES
        )
        path = Path(directory)
        if (
            path.name == "res"
            and path.parent.name == "main"
            and path.parent.parent.name == "src"
        ):
            result.append(path)
            child_names.clear()
    return sorted(result)


def module_name(root: Path, res_root: Path) -> str:
    """Return the module path that owns a conventional src/main/res directory."""

    return res_root.parents[2].relative_to(root).as_posix()


def element_text(element: ElementTree.Element) -> str:
    """Return text including nested xliff:g or styling elements."""

    return "".join(element.itertext()).strip()


def parse_resource_directory(
    directory: Path,
    locale: str,
) -> tuple[dict[ResourceId, Resource], list[Issue]]:
    """Parse supported text resources from all XML files in one values directory."""

    resources: dict[ResourceId, Resource] = {}
    issues: list[Issue] = []
    if not directory.is_dir():
        return resources, issues

    for source in sorted(directory.glob("*.xml")):
        try:
            root = ElementTree.parse(source).getroot()
        except (ElementTree.ParseError, OSError) as error:
            issues.append(Issue(source, locale, f"cannot parse XML: {error}"))
            continue

        for element in root:
            kind = local_name(element.tag)
            if kind not in SUPPORTED_RESOURCE_TYPES:
                continue

            name = element.get("name", "").strip()
            if not name:
                issues.append(Issue(source, locale, f"<{kind}> is missing a name"))
                continue

            resource_id = ResourceId(kind, name)
            if resource_id in resources:
                issues.append(
                    Issue(
                        source,
                        locale,
                        f"duplicate {kind} resource '{name}'",
                    ),
                )
                continue

            items: dict[str, ResourceItem] = {}
            if kind == "string":
                items[""] = ResourceItem(element_text(element), source)
            elif kind == "plurals":
                for item in element:
                    if local_name(item.tag) != "item":
                        continue
                    quantity = item.get("quantity", "").strip()
                    if not quantity:
                        issues.append(
                            Issue(
                                source,
                                locale,
                                f"plural '{name}' has an item without a quantity",
                            ),
                        )
                    elif quantity in items:
                        issues.append(
                            Issue(
                                source,
                                locale,
                                f"plural '{name}' repeats quantity '{quantity}'",
                            ),
                        )
                    else:
                        items[quantity] = ResourceItem(element_text(item), source)
            else:
                for index, item in enumerate(element):
                    if local_name(item.tag) == "item":
                        items[str(index)] = ResourceItem(element_text(item), source)

            if not items:
                issues.append(
                    Issue(source, locale, f"{kind} resource '{name}' has no values"),
                )

            resources[resource_id] = Resource(
                resource_id=resource_id,
                items=items,
                source=source,
                translatable=element.get("translatable", "true").lower() != "false",
            )

    return resources, issues


def load_default_catalogs(
    root: Path,
) -> tuple[list[ModuleCatalog], list[Issue]]:
    """Load every module that owns at least one supported default text resource."""

    catalogs: list[ModuleCatalog] = []
    issues: list[Issue] = []
    for res_root in discover_res_roots(root):
        resources, parse_issues = parse_resource_directory(
            res_root / "values",
            "default",
        )
        issues.extend(parse_issues)
        if resources:
            catalogs.append(
                ModuleCatalog(
                    module=module_name(root, res_root),
                    res_root=res_root,
                    resources=resources,
                ),
            )
    return catalogs, issues


def find_hardcoded_compose_text(root: Path) -> list[Issue]:
    """Find common direct Compose literals while allowing preview-only source files."""

    issues: list[Issue] = []
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
            if source.suffix != ".kt" or "Preview" in source.stem:
                continue
            try:
                lines = source.read_text(encoding="utf-8").splitlines()
            except OSError as error:
                issues.append(
                    Issue(source, "source", f"cannot read Kotlin source: {error}"),
                )
                continue
            for line_number, line in enumerate(lines, start=1):
                if (
                    "localization-ignore" not in line
                    and HARD_CODED_COMPOSE_TEXT_PATTERN.search(line)
                ):
                    issues.append(
                        Issue(
                            source,
                            "source",
                            (
                                f"hardcoded Compose text at line {line_number}; "
                                "move production text to a string resource"
                            ),
                        ),
                    )
    return issues


def discover_locales(catalogs: Sequence[ModuleCatalog]) -> list[str]:
    """Discover locale-only values directories in modules with default text."""

    locales: set[str] = set()
    for catalog in catalogs:
        for candidate in catalog.res_root.glob("values-*"):
            locale = qualifier_to_locale(candidate.name.removeprefix("values-"))
            if locale:
                locales.add(locale)
    return sorted(locales)


def format_arguments(text: str) -> Counter[tuple[int, str]]:
    """Return the indexed Java Formatter arguments consumed by a string."""

    arguments: Counter[tuple[int, str]] = Counter()
    next_index = 1
    previous_index: int | None = None
    for match in FORMAT_ARGUMENT_PATTERN.finditer(text):
        conversion = match.group("conversion")
        if conversion in {"%", "n"}:
            continue

        explicit_index = match.group("index")
        if explicit_index:
            argument_index = int(explicit_index)
        elif "<" in match.group("flags") and previous_index is not None:
            argument_index = previous_index
        else:
            argument_index = next_index
            next_index += 1

        date_prefix = match.group("date_prefix")
        if date_prefix:
            conversion_type = "t" + match.group("date_conversion").lower()
        else:
            conversion_type = conversion.lower()
        arguments[(argument_index, conversion_type)] += 1
        previous_index = argument_index
    return arguments


def item_label(resource: Resource, item: str) -> str:
    """Format an optional plural quantity or array index for diagnostics."""

    if resource.resource_id.kind == "plurals":
        return f" quantity '{item}'"
    if resource.resource_id.kind == "string-array":
        return f" item {item}"
    return ""


def compare_resource(
    base: Resource,
    translation: Resource,
    locale: str,
) -> list[Issue]:
    """Validate structure, non-empty text, and formatter arguments."""

    issues: list[Issue] = []
    missing_items = sorted(set(base.items) - set(translation.items))
    extra_items = sorted(set(translation.items) - set(base.items))

    for item in missing_items:
        issues.append(
            Issue(
                translation.source,
                locale,
                (
                    f"{base.resource_id.kind} '{base.resource_id.name}' is missing"
                    f"{item_label(base, item)}"
                ),
            ),
        )
    if base.resource_id.kind == "string-array":
        for item in extra_items:
            issues.append(
                Issue(
                    translation.source,
                    locale,
                    (
                        f"string-array '{base.resource_id.name}' has unexpected"
                        f"{item_label(base, item)}"
                    ),
                ),
            )

    for item, translated_item in translation.items.items():
        if not translated_item.text:
            issues.append(
                Issue(
                    translated_item.source,
                    locale,
                    (
                        f"{base.resource_id.kind} '{base.resource_id.name}' has an"
                        f" empty translation{item_label(base, item)}"
                    ),
                ),
            )
            continue

        base_item = base.items.get(item)
        if base_item is None and base.resource_id.kind == "plurals":
            base_item = base.items.get("other")
        if base_item is None:
            continue

        base_arguments = format_arguments(base_item.text)
        translated_arguments = format_arguments(translated_item.text)
        if base_arguments != translated_arguments:
            issues.append(
                Issue(
                    translated_item.source,
                    locale,
                    (
                        f"{base.resource_id.kind} '{base.resource_id.name}'"
                        f"{item_label(base, item)} changes format arguments from "
                        f"{sorted(base_arguments.elements())} to "
                        f"{sorted(translated_arguments.elements())}"
                    ),
                ),
            )

    return issues


def validate_locale(
    catalogs: Sequence[ModuleCatalog],
    locale: str,
) -> tuple[list[Issue], int, int]:
    """Validate one locale and return issues, translated count, and total count."""

    issues: list[Issue] = []
    translated_count = 0
    total_count = 0
    qualifier = locale_to_qualifier(locale)

    for catalog in catalogs:
        translations, parse_issues = parse_resource_directory(
            catalog.res_root / f"values-{qualifier}",
            locale,
        )
        issues.extend(parse_issues)
        localizable = {
            resource_id: resource
            for resource_id, resource in catalog.resources.items()
            if resource.translatable
        }
        total_count += len(localizable)

        for resource_id, base in sorted(localizable.items()):
            translation = translations.get(resource_id)
            if translation is None:
                issues.append(
                    Issue(
                        catalog.res_root / f"values-{qualifier}",
                        locale,
                        (
                            f"missing {resource_id.kind} translation "
                            f"'{resource_id.name}' in module '{catalog.module}'"
                        ),
                    ),
                )
                continue
            translated_count += 1
            issues.extend(compare_resource(base, translation, locale))

        for resource_id, translation in sorted(translations.items()):
            base = catalog.resources.get(resource_id)
            if base is None:
                issues.append(
                    Issue(
                        translation.source,
                        locale,
                        (
                            f"{resource_id.kind} translation '{resource_id.name}' "
                            "has no default resource"
                        ),
                    ),
                )
            elif not base.translatable:
                issues.append(
                    Issue(
                        translation.source,
                        locale,
                        (
                            f"{resource_id.kind} '{resource_id.name}' is marked "
                            "translatable=\"false\" in the default resources"
                        ),
                    ),
                )

    return issues, translated_count, total_count


def check_repository(
    root: Path,
    requested_locales: Sequence[str] | None = None,
) -> tuple[list[Issue], dict[str, tuple[int, int]]]:
    """Validate default resources and all requested or discovered locales."""

    resolved_root = root.resolve()
    catalogs, issues = load_default_catalogs(resolved_root)
    issues.extend(find_hardcoded_compose_text(resolved_root))
    if not catalogs:
        issues.append(
            Issue(resolved_root, "default", "no Android text resources were found"),
        )
        return issues, {}

    if requested_locales:
        locales = sorted({canonical_locale(locale) for locale in requested_locales})
    else:
        locales = discover_locales(catalogs)
    if not locales:
        issues.append(
            Issue(
                resolved_root,
                "default",
                "no localized values directories were found",
            ),
        )
        return issues, {}

    coverage: dict[str, tuple[int, int]] = {}
    for locale in locales:
        locale_issues, translated_count, total_count = validate_locale(
            catalogs,
            locale,
        )
        issues.extend(locale_issues)
        coverage[locale] = (translated_count, total_count)
    return issues, coverage


def report_status(base: ResourceItem, translation: ResourceItem | None) -> str:
    """Return a compact per-item status for translation reports."""

    if translation is None:
        return "missing"
    if not translation.text:
        return "empty"
    if format_arguments(base.text) != format_arguments(translation.text):
        return "format-mismatch"
    return "translated"


def build_report(root: Path, locale: str) -> tuple[list[ReportRow], list[Issue]]:
    """Build a leaf-level report for one locale."""

    resolved_root = root.resolve()
    canonical = canonical_locale(locale)
    qualifier = locale_to_qualifier(canonical)
    catalogs, issues = load_default_catalogs(resolved_root)
    rows: list[ReportRow] = []

    for catalog in catalogs:
        translations, parse_issues = parse_resource_directory(
            catalog.res_root / f"values-{qualifier}",
            canonical,
        )
        issues.extend(parse_issues)
        for resource_id, base in sorted(catalog.resources.items()):
            if not base.translatable:
                continue
            translation = translations.get(resource_id)
            for item, base_item in sorted(base.items.items()):
                translated_item = translation.items.get(item) if translation else None
                rows.append(
                    ReportRow(
                        locale=canonical,
                        module=catalog.module,
                        resource_type=resource_id.kind,
                        key=resource_id.name,
                        item=item,
                        source_text=base_item.text,
                        translation=translated_item.text if translated_item else "",
                        status=report_status(base_item, translated_item),
                        source_file=str(base_item.source.relative_to(resolved_root)),
                        translation_file=(
                            str(translated_item.source.relative_to(resolved_root))
                            if translated_item
                            else ""
                        ),
                    ),
                )
    return rows, issues


def write_report(rows: Sequence[ReportRow], output_format: str, stream: TextIO) -> None:
    """Write report rows in a human-readable or machine-readable format."""

    if output_format == "json":
        json.dump(
            [asdict(row) for row in rows],
            stream,
            ensure_ascii=False,
            indent=2,
        )
        stream.write("\n")
        return
    if output_format == "csv":
        field_names = list(ReportRow.__dataclass_fields__)
        writer = csv.DictWriter(stream, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
        return

    translated = sum(row.status == "translated" for row in rows)
    stream.write(f"Locale: {rows[0].locale if rows else 'unknown'}\n")
    stream.write(f"Translated values: {translated}/{len(rows)}\n")
    for row in rows:
        marker = "OK" if row.status == "translated" else row.status.upper()
        item = f"[{row.item}]" if row.item else ""
        stream.write(
            f"{marker:15} {row.module}:"
            f"{row.resource_type}/{row.key}{item}\n",
        )


def print_issues(issues: Iterable[Issue], root: Path) -> None:
    """Print compiler-style failures with stable repository-relative paths."""

    resolved_root = root.resolve()
    for issue in issues:
        try:
            path = issue.path.resolve().relative_to(resolved_root)
        except ValueError:
            path = issue.path
        print(
            f"{path}: error: [{issue.locale}] {issue.message}",
            file=sys.stderr,
        )


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line interface."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate Android string, plurals, and string-array translations "
            "across every module."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="repository root (default: current directory)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser(
        "check",
        help="fail on missing, stale, empty, or format-incompatible translations",
    )
    check_parser.add_argument(
        "--locale",
        action="append",
        dest="locales",
        help="BCP 47 locale to check; repeat as needed (default: discover all)",
    )

    report_parser = subparsers.add_parser(
        "report",
        help="export translation coverage and source text",
    )
    report_parser.add_argument("--locale", required=True, help="BCP 47 locale")
    report_parser.add_argument(
        "--format",
        choices=("table", "csv", "json"),
        default="table",
        dest="output_format",
    )
    report_parser.add_argument(
        "--output",
        type=Path,
        help="write the report to this file instead of stdout",
    )
    return parser


def run(arguments: argparse.Namespace) -> int:
    """Run the requested command and return a process exit code."""

    if arguments.command == "check":
        issues, coverage = check_repository(arguments.root, arguments.locales)
        if issues:
            print_issues(issues, arguments.root)
            return 1
        summary = ", ".join(
            f"{locale} {translated}/{total}"
            for locale, (translated, total) in coverage.items()
        )
        print(f"Localization check passed: {summary} translated resources.")
        return 0

    rows, issues = build_report(arguments.root, arguments.locale)
    if issues:
        print_issues(issues, arguments.root)
        return 1
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        with arguments.output.open("w", encoding="utf-8", newline="") as stream:
            write_report(rows, arguments.output_format, stream)
        print(f"Wrote localization report to {arguments.output}")
    else:
        write_report(rows, arguments.output_format, sys.stdout)
    return 0


def main() -> int:
    """Parse arguments and run the localization tool."""

    try:
        return run(create_parser().parse_args())
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
