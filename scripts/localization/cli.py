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
"""Command-line interface for the repository localization tool."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Sequence, TextIO

from .core import (
    Issue,
    ReportRow,
    build_report,
    check_repository,
)
from .exchange import export_xliff, import_translations
from .orphans import find_orphans
from .report import build_model, render_html, write_html_report
from .warnings import collect_warnings
from .writer import (
    WriteError,
    add_default_string,
    apply_translation,
    scaffold_locale,
)


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


def print_warnings(root: Path, requested_locales: Sequence[str] | None) -> int:
    """Print non-fatal quality warnings; return the number reported."""

    resolved_root = root.resolve()
    warnings = collect_warnings(resolved_root, requested_locales)
    for warning in warnings:
        try:
            path = warning.path.resolve().relative_to(resolved_root)
        except ValueError:
            path = warning.path
        print(
            f"{path}: warning: [{warning.locale}] "
            f"({warning.category}) {warning.message}",
            file=sys.stderr,
        )
    return len(warnings)


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
    check_parser.add_argument(
        "--warnings",
        action="store_true",
        help="also print non-fatal quality warnings (does not affect exit code)",
    )

    report_parser = subparsers.add_parser(
        "report",
        help="export translation coverage and source text",
    )
    report_parser.add_argument(
        "--locale",
        help="BCP 47 locale (required for table, csv, json; optional for html)",
    )
    report_parser.add_argument(
        "--format",
        choices=("table", "csv", "json", "html", "xliff"),
        default="table",
        dest="output_format",
    )
    report_parser.add_argument(
        "--output",
        type=Path,
        help="write the report to this file instead of stdout",
    )

    add_string_parser = subparsers.add_parser(
        "add-string",
        help="add a new default <string> to a module (minimal-diff edit)",
    )
    add_string_parser.add_argument("--module", required=True, help="owning module path")
    add_string_parser.add_argument("--name", required=True, help="resource name")
    add_string_parser.add_argument("--text", required=True, help="default value")
    add_string_parser.add_argument(
        "--file",
        default="strings.xml",
        help="values file to edit (default: strings.xml)",
    )
    add_string_parser.add_argument(
        "--not-translatable",
        action="store_true",
        help='mark the string translatable="false"',
    )

    add_locale_parser = subparsers.add_parser(
        "add-locale",
        help="scaffold a new locale's files across every owning module",
    )
    add_locale_parser.add_argument("locale", help="BCP 47 locale to scaffold")
    add_locale_parser.add_argument(
        "--fill",
        choices=("source", "empty"),
        default="source",
        help="initial value for each key (default: source text)",
    )
    add_locale_parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        help="limit scaffolding to this module; repeat as needed",
    )

    set_parser = subparsers.add_parser(
        "set",
        help="set one translation value (minimal-diff edit)",
    )
    set_parser.add_argument("--locale", required=True, help="BCP 47 locale")
    set_parser.add_argument("--module", required=True, help="owning module path")
    set_parser.add_argument("--name", required=True, help="resource name")
    set_parser.add_argument("--text", required=True, help="translated value")
    set_parser.add_argument(
        "--file",
        default="strings.xml",
        help="values file to edit (default: strings.xml)",
    )

    import_parser = subparsers.add_parser(
        "import",
        help="import a filled CSV or XLIFF file into a locale (minimal-diff edits)",
    )
    import_parser.add_argument("--locale", required=True, help="BCP 47 locale")
    import_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        dest="input_path",
        help="CSV or XLIFF file to import",
    )
    import_parser.add_argument(
        "--format",
        choices=("auto", "csv", "xliff"),
        default="auto",
        dest="input_format",
        help="input format (default: infer from the file extension)",
    )

    subparsers.add_parser(
        "orphans",
        help="list default resources with no reference found in source",
    )

    serve_parser = subparsers.add_parser(
        "serve",
        help="run the local web wizard (requires the web extras)",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="bind host")
    serve_parser.add_argument("--port", type=int, default=8080, help="bind port")
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="enable auto-reload for development",
    )
    return parser


def run(arguments: argparse.Namespace) -> int:
    """Run the requested command and return a process exit code."""

    if arguments.command == "check":
        issues, coverage = check_repository(arguments.root, arguments.locales)
        if issues:
            print_issues(issues, arguments.root)
            if arguments.warnings:
                print_warnings(arguments.root, arguments.locales)
            return 1
        summary = ", ".join(
            f"{locale} {translated}/{total}"
            for locale, (translated, total) in coverage.items()
        )
        print(f"Localization check passed: {summary} translated resources.")
        if arguments.warnings:
            count = print_warnings(arguments.root, arguments.locales)
            print(f"{count} quality warning(s) reported.")
        return 0

    if arguments.command == "report":
        return run_report(arguments)
    if arguments.command == "add-string":
        return run_add_string(arguments)
    if arguments.command == "add-locale":
        return run_add_locale(arguments)
    if arguments.command == "set":
        return run_set(arguments)
    if arguments.command == "import":
        return run_import(arguments)
    if arguments.command == "orphans":
        return run_orphans(arguments)
    return run_serve(arguments)


def run_add_string(arguments: argparse.Namespace) -> int:
    """Add a new default string to a module, preserving file formatting."""

    translatable = False if arguments.not_translatable else None
    try:
        target = add_default_string(
            arguments.root,
            arguments.module,
            arguments.name,
            arguments.text,
            translatable,
            arguments.file,
        )
    except WriteError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Added string '{arguments.name}' to {target}")
    return 0


def run_add_locale(arguments: argparse.Namespace) -> int:
    """Scaffold a new locale across every owning module."""

    created, skipped = scaffold_locale(
        arguments.root,
        arguments.locale,
        arguments.fill,
        arguments.modules,
    )
    for path in created:
        print(f"Created {path}")
    for path in skipped:
        print(f"Skipped existing {path}")
    if not created and not skipped:
        print("No modules with translatable resources were found.")
    return 0


def run_set(arguments: argparse.Namespace) -> int:
    """Set one translation value, updating or adding the key in place."""

    try:
        action, target = apply_translation(
            arguments.root,
            arguments.locale,
            arguments.module,
            arguments.name,
            arguments.text,
            arguments.file,
        )
    except WriteError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(
        f"{action.capitalize()} '{arguments.name}' [{arguments.locale}] in {target}",
    )
    return 0


def run_import(arguments: argparse.Namespace) -> int:
    """Import a CSV or XLIFF file's translations into a locale."""

    if not arguments.input_path.is_file():
        print(f"error: {arguments.input_path} does not exist", file=sys.stderr)
        return 2
    try:
        summary = import_translations(
            arguments.root,
            arguments.locale,
            arguments.input_path,
            arguments.input_format,
        )
    except (ValueError, WriteError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(
        f"Imported [{arguments.locale}]: {summary.applied} applied, "
        f"{summary.unchanged} unchanged, {summary.skipped_empty} empty skipped "
        f"across {len(summary.written_files)} file(s).",
    )
    for entry in summary.unsupported:
        print(f"  skipped: {entry}", file=sys.stderr)
    return 0


def run_orphans(arguments: argparse.Namespace) -> int:
    """List default resources with no discovered reference in source."""

    orphans = find_orphans(arguments.root)
    for orphan in orphans:
        print(
            f"{orphan.module}: {orphan.resource_id.kind}/{orphan.resource_id.name}",
        )
    print(f"{len(orphans)} unused key(s) found.")
    return 0


def run_serve(arguments: argparse.Namespace) -> int:
    """Launch the local web wizard, importing the web extras lazily."""

    try:
        import uvicorn  # noqa: PLC0415

        from .web import create_app  # noqa: PLC0415
    except ImportError:
        print(
            "error: the web wizard needs FastAPI and uvicorn. Install them with\n"
            "  python3 -m pip install -r tools/localization-web/requirements.txt",
            file=sys.stderr,
        )
        return 2

    os.environ["LOCALIZATION_ROOT"] = str(arguments.root.resolve())
    if arguments.reload:
        uvicorn.run(
            "localization.web:app",
            host=arguments.host,
            port=arguments.port,
            reload=True,
        )
    else:
        uvicorn.run(
            create_app(arguments.root.resolve()),
            host=arguments.host,
            port=arguments.port,
        )
    return 0


def run_report(arguments: argparse.Namespace) -> int:
    """Run the report command for one locale or an all-locale HTML dashboard."""

    locales = [arguments.locale] if arguments.locale else None

    if arguments.output_format == "html":
        if arguments.output:
            model = write_html_report(arguments.root, arguments.output, locales)
            print(
                f"Wrote localization report to {arguments.output} "
                f"({model.translated}/{model.total} translated).",
            )
        else:
            sys.stdout.write(render_html(build_model(arguments.root, locales)))
        return 0

    if not arguments.locale:
        print(
            "error: --locale is required for table, csv, json, and xliff formats",
            file=sys.stderr,
        )
        return 2

    if arguments.output_format == "xliff":
        document, issues = export_xliff(arguments.root, arguments.locale)
        if issues:
            print_issues(issues, arguments.root)
            return 1
        if arguments.output:
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_text(document, encoding="utf-8")
            print(f"Wrote localization report to {arguments.output}")
        else:
            sys.stdout.write(document)
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
