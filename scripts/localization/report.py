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
"""Generate a self-contained localization status report as a single HTML file.

The report aggregates every discovered (or requested) locale: an overall
coverage summary, a locale x module coverage matrix, the errors from
:mod:`localization.core`, the warnings from :mod:`localization.warnings`, and a
searchable per-locale table of every translatable value. The output inlines all
CSS and JavaScript so it can be published as a CI build artifact without any
external assets.
"""

from __future__ import annotations

import datetime
import html
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .core import (
    ReportRow,
    build_report,
    canonical_locale,
    check_repository,
    discover_locales,
    load_default_catalogs,
)
from .orphans import Orphan, find_orphans
from .warnings import LintWarning, collect_warnings


STATUS_LABELS = {
    "translated": "Translated",
    "missing": "Missing",
    "empty": "Empty",
    "format-mismatch": "Format mismatch",
}


@dataclass(frozen=True)
class LocaleSummary:
    """Aggregated status for one locale used by the report."""

    locale: str
    rows: list[ReportRow]
    warnings: list[LintWarning]
    translated: int
    total: int

    @property
    def percent(self) -> float:
        """Return the translated percentage, or 100 when there is nothing to do."""

        return 100.0 if self.total == 0 else 100.0 * self.translated / self.total


@dataclass(frozen=True)
class ReportModel:
    """Everything the HTML template needs, computed once from the repository."""

    generated_at: str
    modules: list[str]
    locales: list[LocaleSummary]
    errors: list[str]
    orphans: list[Orphan]

    @property
    def translated(self) -> int:
        return sum(locale.translated for locale in self.locales)

    @property
    def total(self) -> int:
        return sum(locale.total for locale in self.locales)

    @property
    def percent(self) -> float:
        return 100.0 if self.total == 0 else 100.0 * self.translated / self.total


def build_model(
    root: Path,
    requested_locales: Sequence[str] | None = None,
) -> ReportModel:
    """Compute the full report model for every discovered or requested locale."""

    resolved_root = root.resolve()
    catalogs, _ = load_default_catalogs(resolved_root)
    modules = sorted(catalog.module for catalog in catalogs)

    if requested_locales:
        locales = sorted({canonical_locale(locale) for locale in requested_locales})
    else:
        locales = discover_locales(catalogs)

    issues, _ = check_repository(resolved_root, requested_locales)
    errors = [
        f"{_relative(issue.path, resolved_root)}: [{issue.locale}] {issue.message}"
        for issue in issues
    ]
    warnings = collect_warnings(resolved_root, requested_locales)

    summaries: list[LocaleSummary] = []
    for locale in locales:
        rows, _ = build_report(resolved_root, locale)
        translated = sum(row.status == "translated" for row in rows)
        summaries.append(
            LocaleSummary(
                locale=locale,
                rows=rows,
                warnings=[w for w in warnings if w.locale == locale],
                translated=translated,
                total=len(rows),
            ),
        )

    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC",
    )
    return ReportModel(
        generated_at=generated_at,
        modules=modules,
        locales=summaries,
        errors=errors,
        orphans=find_orphans(resolved_root),
    )


def _relative(path: Path, root: Path) -> str:
    """Return a repository-relative path when possible, else the original."""

    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _coverage_class(percent: float) -> str:
    """Map a coverage percentage to a heat CSS class."""

    if percent >= 100.0:
        return "heat-full"
    if percent >= 75.0:
        return "heat-high"
    if percent >= 40.0:
        return "heat-mid"
    if percent > 0.0:
        return "heat-low"
    return "heat-none"


def _module_percent(summary: LocaleSummary, module: str) -> tuple[float, int, int]:
    """Return coverage percent, translated, and total for one module in a locale."""

    rows = [row for row in summary.rows if row.module == module]
    translated = sum(row.status == "translated" for row in rows)
    total = len(rows)
    percent = 100.0 if total == 0 else 100.0 * translated / total
    return percent, translated, total


def render_html(model: ReportModel) -> str:
    """Render the report model to a single self-contained HTML document."""

    parts: list[str] = []
    parts.append("<!doctype html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('<meta charset="utf-8">')
    parts.append(
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
    )
    parts.append("<title>Localization status</title>")
    parts.append(f"<style>{_STYLE}</style>")
    parts.append("</head>")
    parts.append("<body>")
    parts.append(_render_header(model))
    parts.append(_render_matrix(model))
    parts.append(_render_diagnostics(model))
    parts.append(_render_orphans(model))
    parts.append(_render_locale_tables(model))
    parts.append(f"<script>{_SCRIPT}</script>")
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts) + "\n"


def _render_header(model: ReportModel) -> str:
    total_warnings = sum(len(locale.warnings) for locale in model.locales)
    cards = [
        _stat_card("Locales", str(len(model.locales))),
        _stat_card("Modules", str(len(model.modules))),
        _stat_card(
            "Coverage",
            f"{model.percent:.0f}%",
            f"{model.translated}/{model.total} values",
        ),
        _stat_card("Errors", str(len(model.errors)), tone=_tone(len(model.errors))),
        _stat_card("Warnings", str(total_warnings), tone=_tone(total_warnings)),
        _stat_card(
            "Unused keys",
            str(len(model.orphans)),
            tone=_tone(len(model.orphans)),
        ),
    ]
    return (
        "<header>"
        "<h1>Localization status</h1>"
        f'<p class="generated">Generated {html.escape(model.generated_at)}</p>'
        f'<div class="cards">{"".join(cards)}</div>'
        "</header>"
    )


def _tone(count: int) -> str:
    return "ok" if count == 0 else "warn"


def _stat_card(label: str, value: str, sub: str = "", tone: str = "") -> str:
    tone_class = f" {tone}" if tone else ""
    sub_html = f'<span class="sub">{html.escape(sub)}</span>' if sub else ""
    return (
        f'<div class="card{tone_class}">'
        f'<span class="value">{html.escape(value)}</span>'
        f'<span class="label">{html.escape(label)}</span>'
        f"{sub_html}"
        "</div>"
    )


def _render_matrix(model: ReportModel) -> str:
    if not model.locales or not model.modules:
        return ""
    head = "".join(
        f"<th>{html.escape(module)}</th>" for module in model.modules
    )
    body_rows: list[str] = []
    for locale in model.locales:
        cells = [
            f'<th scope="row">{html.escape(locale.locale)}</th>',
            f'<td class="{_coverage_class(locale.percent)} total">'
            f"{locale.percent:.0f}%</td>",
        ]
        for module in model.modules:
            percent, translated, total = _module_percent(locale, module)
            title = f"{translated}/{total} values"
            cells.append(
                f'<td class="{_coverage_class(percent)}" title="{html.escape(title)}">'
                f"{percent:.0f}%</td>",
            )
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    return (
        "<section>"
        "<h2>Coverage matrix</h2>"
        '<div class="scroll">'
        '<table class="matrix">'
        f"<thead><tr><th>Locale</th><th>Overall</th>{head}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
        "</section>"
    )


def _render_diagnostics(model: ReportModel) -> str:
    sections: list[str] = []
    if model.errors:
        items = "".join(f"<li>{html.escape(error)}</li>" for error in model.errors)
        sections.append(
            '<details open class="diagnostics errors">'
            f"<summary>Errors ({len(model.errors)})</summary>"
            f"<ul>{items}</ul>"
            "</details>",
        )
    warnings = [w for locale in model.locales for w in locale.warnings]
    if warnings:
        items = "".join(
            f'<li><span class="tag">{html.escape(w.category)}</span> '
            f"[{html.escape(w.locale)}] {html.escape(w.message)}</li>"
            for w in warnings
        )
        sections.append(
            '<details class="diagnostics warnings">'
            f"<summary>Warnings ({len(warnings)})</summary>"
            f"<ul>{items}</ul>"
            "</details>",
        )
    if not sections:
        return (
            "<section><h2>Diagnostics</h2>"
            '<p class="empty">No errors or warnings.</p></section>'
        )
    return f"<section><h2>Diagnostics</h2>{''.join(sections)}</section>"


def _render_orphans(model: ReportModel) -> str:
    if not model.orphans:
        return ""
    items = "".join(
        f"<li>{html.escape(orphan.module)}: "
        f"{html.escape(orphan.resource_id.kind)}/"
        f"{html.escape(orphan.resource_id.name)}</li>"
        for orphan in model.orphans
    )
    return (
        "<section><h2>Unused keys</h2>"
        '<p class="empty">Default resources with no reference found in source. '
        "Dynamic lookups cannot be detected, so review before removing.</p>"
        f"<details><summary>Unused keys ({len(model.orphans)})</summary>"
        f"<ul>{items}</ul></details>"
        "</section>"
    )


def _render_locale_tables(model: ReportModel) -> str:
    if not model.locales:
        return '<section><p class="empty">No locales found.</p></section>'
    blocks: list[str] = []
    for locale in model.locales:
        rows_html = "".join(_render_row(row) for row in locale.rows)
        blocks.append(
            "<details open>"
            f"<summary>{html.escape(locale.locale)} "
            f"&mdash; {locale.translated}/{locale.total} "
            f"({locale.percent:.0f}%)</summary>"
            '<div class="scroll"><table class="values">'
            "<thead><tr><th>Module</th><th>Key</th><th>Source</th>"
            "<th>Translation</th><th>Status</th></tr></thead>"
            f"<tbody>{rows_html}</tbody>"
            "</table></div>"
            "</details>",
        )
    controls = (
        '<div class="controls">'
        '<input type="search" id="filter" placeholder="Filter by key or text…" '
        'aria-label="Filter rows">'
        '<label><input type="checkbox" id="untranslated-only"> '
        "Show only untranslated</label>"
        "</div>"
    )
    return f"<section><h2>Values</h2>{controls}{''.join(blocks)}</section>"


def _render_row(row: ReportRow) -> str:
    key = html.escape(row.key)
    if row.item:
        key += f' <span class="item">[{html.escape(row.item)}]</span>'
    status_label = STATUS_LABELS.get(row.status, row.status)
    return (
        f'<tr data-status="{html.escape(row.status)}">'
        f"<td>{html.escape(row.module)}</td>"
        f"<td>{key}</td>"
        f'<td class="text">{html.escape(row.source_text)}</td>'
        f'<td class="text">{html.escape(row.translation)}</td>'
        f'<td><span class="badge {html.escape(row.status)}">'
        f"{html.escape(status_label)}</span></td>"
        "</tr>"
    )


def write_html_report(
    root: Path,
    output: Path,
    requested_locales: Sequence[str] | None = None,
) -> ReportModel:
    """Build and write the HTML report, returning the model for callers."""

    model = build_model(root, requested_locales)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(model), encoding="utf-8")
    return model


# Palette tokens are declared once and reused for the OS preference media query
# and for the explicit data-theme overrides a host may stamp on the root element.
_LIGHT_TOKENS = (
    "--bg: #f6f7f9; --surface: #ffffff; --border: #e2e5ea; --text: #1b1f24; "
    "--muted: #626a75; --accent: #2f6feb; --ok: #1f8b4c; --warn: #b26a00; "
    "--err: #c0392b; "
    "--heat-full: #d6f0dd; --heat-high: #e3f2d4; --heat-mid: #fdf1c8; "
    "--heat-low: #fbe0cf; --heat-none: #f7d4d4;"
)
_DARK_TOKENS = (
    "--bg: #14171c; --surface: #1c2027; --border: #2b313a; --text: #e6e9ee; "
    "--muted: #9aa4b1; --accent: #6ea0ff; --ok: #57c98a; --warn: #e0a44a; "
    "--err: #f0776a; "
    "--heat-full: #1e4433; --heat-high: #35431f; --heat-mid: #4a3f14; "
    "--heat-low: #4a2f1c; --heat-none: #4a2222;"
)
_RULES = """
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2rem 1.5rem 4rem; background: var(--bg); color: var(--text);
  font: 15px/1.5 system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
}
h1 { margin: 0 0 .25rem; font-size: 1.6rem; }
h2 { margin: 2.2rem 0 .8rem; font-size: 1.2rem; }
.generated { color: var(--muted); margin: 0 0 1.2rem; }
.cards { display: flex; flex-wrap: wrap; gap: .8rem; }
.card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: .8rem 1rem; min-width: 7rem; display: flex; flex-direction: column;
}
.card .value { font-size: 1.6rem; font-weight: 600; }
.card .label { color: var(--muted); font-size: .85rem; }
.card .sub { color: var(--muted); font-size: .75rem; }
.card.ok .value { color: var(--ok); }
.card.warn .value { color: var(--warn); }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; background: var(--surface); }
th, td {
  border: 1px solid var(--border); padding: .45rem .6rem; text-align: left;
  vertical-align: top;
}
.matrix td { text-align: center; font-variant-numeric: tabular-nums; white-space: nowrap; }
.matrix .total { font-weight: 600; }
.heat-full { background: var(--heat-full); }
.heat-high { background: var(--heat-high); }
.heat-mid { background: var(--heat-mid); }
.heat-low { background: var(--heat-low); }
.heat-none { background: var(--heat-none); }
.values .text { max-width: 26rem; white-space: pre-wrap; word-break: break-word; }
.item { color: var(--muted); }
.badge {
  display: inline-block; padding: .1rem .5rem; border-radius: 999px;
  font-size: .78rem; font-weight: 600;
}
.badge.translated { background: var(--heat-full); color: var(--ok); }
.badge.missing { background: var(--heat-none); color: var(--err); }
.badge.empty { background: var(--heat-low); color: var(--warn); }
.badge.format-mismatch { background: var(--heat-mid); color: var(--warn); }
.controls { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; margin-bottom: 1rem; }
.controls input[type=search] {
  padding: .5rem .7rem; border: 1px solid var(--border); border-radius: 8px;
  background: var(--surface); color: var(--text); min-width: 16rem;
}
details { margin: .6rem 0; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
summary {
  cursor: pointer; padding: .7rem 1rem; background: var(--surface); font-weight: 600;
}
details .scroll, details ul { padding: 0 1rem 1rem; }
.diagnostics ul { margin: .4rem 0 0; }
.diagnostics.errors summary { color: var(--err); }
.diagnostics.warnings summary { color: var(--warn); }
.tag {
  display: inline-block; padding: 0 .4rem; border-radius: 4px; font-size: .72rem;
  background: var(--heat-mid); color: var(--warn); margin-right: .3rem;
}
.empty { color: var(--muted); }
"""

_STYLE = (
    ":root { color-scheme: light dark; " + _LIGHT_TOKENS + " }\n"
    "@media (prefers-color-scheme: dark) { :root { " + _DARK_TOKENS + " } }\n"
    ':root[data-theme="dark"] { ' + _DARK_TOKENS + " }\n"
    ':root[data-theme="light"] { ' + _LIGHT_TOKENS + " }\n"
    + _RULES
)

_SCRIPT = """
const filter = document.getElementById('filter');
const untranslatedOnly = document.getElementById('untranslated-only');
function apply() {
  const term = (filter.value || '').toLowerCase();
  const only = untranslatedOnly.checked;
  document.querySelectorAll('table.values tbody tr').forEach(function (row) {
    const matchesTerm = !term || row.textContent.toLowerCase().includes(term);
    const matchesStatus = !only || row.dataset.status !== 'translated';
    row.style.display = matchesTerm && matchesStatus ? '' : 'none';
  });
}
if (filter && untranslatedOnly) {
  filter.addEventListener('input', apply);
  untranslatedOnly.addEventListener('change', apply);
}
"""
