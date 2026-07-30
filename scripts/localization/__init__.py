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
"""Android localization tooling: parsing, validation, reporting, and authoring.

The public surface re-exports the parsing and validation core so existing
callers can keep using ``import localization`` while the implementation grows
into focused submodules (``core``, ``cli``, and later ``report``, ``writer``,
``warnings``, ``orphans``, ``exchange``, and ``web``).
"""

from __future__ import annotations

from .cli import (
    create_parser,
    main,
    print_issues,
    print_warnings,
    run,
    run_add_locale,
    run_add_string,
    run_import,
    run_orphans,
    run_report,
    run_serve,
    run_set,
    write_report,
)
from .core import (
    IGNORED_DIRECTORY_NAMES,
    SUPPORTED_RESOURCE_TYPES,
    Issue,
    ModuleCatalog,
    ReportRow,
    Resource,
    ResourceId,
    ResourceItem,
    build_report,
    canonical_locale,
    check_repository,
    compare_resource,
    discover_locales,
    discover_res_roots,
    element_text,
    find_hardcoded_compose_text,
    format_arguments,
    item_label,
    load_default_catalogs,
    local_name,
    locale_to_qualifier,
    module_name,
    parse_resource_directory,
    qualifier_to_locale,
    report_status,
    validate_locale,
)
from .exchange import (
    ImportSummary,
    export_xliff,
    import_translations,
    render_xliff,
    resolve_format,
)
from .orphans import Orphan, collect_references, find_orphans
from .report import (
    LocaleSummary,
    ReportModel,
    build_model,
    render_html,
    write_html_report,
)
from .warnings import LintWarning, collect_warnings
from .writer import (
    WriteError,
    add_default_string,
    add_string,
    apply_translation,
    escape_android_text,
    extract_header,
    find_res_root,
    has_string,
    render_resource_file,
    scaffold_locale,
    set_string_value,
)

__all__ = [
    "IGNORED_DIRECTORY_NAMES",
    "SUPPORTED_RESOURCE_TYPES",
    "ImportSummary",
    "Issue",
    "LintWarning",
    "LocaleSummary",
    "ModuleCatalog",
    "Orphan",
    "ReportModel",
    "ReportRow",
    "Resource",
    "ResourceId",
    "ResourceItem",
    "WriteError",
    "add_default_string",
    "add_string",
    "apply_translation",
    "build_model",
    "build_report",
    "canonical_locale",
    "check_repository",
    "collect_references",
    "collect_warnings",
    "compare_resource",
    "create_parser",
    "discover_locales",
    "discover_res_roots",
    "element_text",
    "escape_android_text",
    "export_xliff",
    "extract_header",
    "find_hardcoded_compose_text",
    "find_orphans",
    "find_res_root",
    "format_arguments",
    "has_string",
    "import_translations",
    "item_label",
    "load_default_catalogs",
    "local_name",
    "locale_to_qualifier",
    "main",
    "module_name",
    "parse_resource_directory",
    "print_issues",
    "print_warnings",
    "qualifier_to_locale",
    "render_html",
    "render_resource_file",
    "render_xliff",
    "report_status",
    "resolve_format",
    "run",
    "run_add_locale",
    "run_add_string",
    "run_import",
    "run_orphans",
    "run_report",
    "run_serve",
    "run_set",
    "scaffold_locale",
    "set_string_value",
    "validate_locale",
    "write_html_report",
    "write_report",
]
