import { useCallback, useEffect, useMemo, useState } from "react";
import {
  addLocale,
  addString,
  getCatalog,
  getLocale,
  setTranslation,
  type Catalog,
  type LocaleDetail,
  type LocaleWarning,
  type Row,
} from "./api";

const STATUS_LABEL: Record<string, string> = {
  translated: "Translated",
  missing: "Missing",
  empty: "Empty",
  "format-mismatch": "Format mismatch",
};

export function App() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [tag, setTag] = useState<string>("");
  const [detail, setDetail] = useState<LocaleDetail | null>(null);
  const [moduleFilter, setModuleFilter] = useState<string>("");
  const [term, setTerm] = useState<string>("");
  const [untranslatedOnly, setUntranslatedOnly] = useState(false);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  const loadCatalog = useCallback(async () => {
    try {
      const next = await getCatalog();
      setCatalog(next);
      setTag((current) =>
        current || (next.locales[0] ? next.locales[0].tag : ""),
      );
    } catch (err) {
      setError(String(err));
    }
  }, []);

  const loadDetail = useCallback(async (which: string) => {
    if (!which) {
      setDetail(null);
      return;
    }
    try {
      setDetail(await getLocale(which));
    } catch (err) {
      setError(String(err));
    }
  }, []);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  useEffect(() => {
    void loadDetail(tag);
  }, [tag, loadDetail]);

  const save = useCallback(
    async (row: Row, text: string) => {
      setError("");
      try {
        const result = await setTranslation({
          locale: tag,
          module: row.module,
          name: row.key,
          text,
        });
        setMessage(`${result.action} ${row.module}:${row.key}`);
        await Promise.all([loadDetail(tag), loadCatalog()]);
      } catch (err) {
        setError(String(err));
      }
    },
    [tag, loadDetail, loadCatalog],
  );

  const onAddLocale = useCallback(async () => {
    const next = window.prompt("New locale (BCP 47, e.g. es or pt-BR):");
    if (!next) return;
    const fill = window.confirm(
      "Fill new keys with the source text?\nOK = copy source, Cancel = leave empty.",
    )
      ? "source"
      : "empty";
    setError("");
    try {
      const result = await addLocale({ locale: next, fill });
      setMessage(`Created ${result.created.length} file(s) for ${next}`);
      await loadCatalog();
      setTag(next);
    } catch (err) {
      setError(String(err));
    }
  }, [loadCatalog]);

  const onAddString = useCallback(async () => {
    if (!catalog) return;
    const moduleName = window.prompt(
      `Module (${catalog.modules.join(", ")}):`,
      catalog.modules[0],
    );
    if (!moduleName) return;
    const name = window.prompt("Resource name:");
    if (!name) return;
    const text = window.prompt("Default (English) value:");
    if (text === null) return;
    setError("");
    try {
      await addString({ module: moduleName, name, text });
      setMessage(`Added ${moduleName}:${name}`);
      await Promise.all([loadCatalog(), loadDetail(tag)]);
    } catch (err) {
      setError(String(err));
    }
  }, [catalog, tag, loadCatalog, loadDetail]);

  const warningsByRow = useMemo(() => {
    const index = new Map<string, LocaleWarning[]>();
    for (const warning of detail?.warnings ?? []) {
      const match = warning.message.match(/'([^']+)'/);
      const key = match ? `${warning.module}:${match[1]}` : "";
      if (!key) continue;
      const list = index.get(key) ?? [];
      list.push(warning);
      index.set(key, list);
    }
    return index;
  }, [detail]);

  const rows = useMemo(() => {
    const all = detail?.rows ?? [];
    const needle = term.trim().toLowerCase();
    return all.filter((row) => {
      if (moduleFilter && row.module !== moduleFilter) return false;
      if (untranslatedOnly && row.status === "translated") return false;
      if (!needle) return true;
      return (
        row.key.toLowerCase().includes(needle) ||
        row.source_text.toLowerCase().includes(needle) ||
        row.translation.toLowerCase().includes(needle)
      );
    });
  }, [detail, moduleFilter, term, untranslatedOnly]);

  return (
    <div className="app">
      <header>
        <div className="titlebar">
          <h1>Localization wizard</h1>
          {catalog && (
            <span className="generated">Updated {catalog.generated_at}</span>
          )}
        </div>
        {catalog && <Cards catalog={catalog} />}
      </header>

      {error && <div className="banner error">{error}</div>}
      {message && !error && <div className="banner ok">{message}</div>}
      {catalog?.errors.length ? (
        <details className="banner warn">
          <summary>{catalog.errors.length} resource error(s)</summary>
          <ul>
            {catalog.errors.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </details>
      ) : null}

      <div className="controls">
        <label>
          Locale
          <select value={tag} onChange={(event) => setTag(event.target.value)}>
            {catalog?.locales.map((locale) => (
              <option key={locale.tag} value={locale.tag}>
                {locale.tag} — {locale.percent}%
              </option>
            ))}
          </select>
        </label>
        <label>
          Module
          <select
            value={moduleFilter}
            onChange={(event) => setModuleFilter(event.target.value)}
          >
            <option value="">All modules</option>
            {catalog?.modules.map((moduleName) => (
              <option key={moduleName} value={moduleName}>
                {moduleName}
              </option>
            ))}
          </select>
        </label>
        <input
          type="search"
          placeholder="Filter by key or text…"
          value={term}
          onChange={(event) => setTerm(event.target.value)}
        />
        <label className="check">
          <input
            type="checkbox"
            checked={untranslatedOnly}
            onChange={(event) => setUntranslatedOnly(event.target.checked)}
          />
          Untranslated only
        </label>
        <span className="spacer" />
        <button type="button" onClick={onAddString}>
          Add string
        </button>
        <button type="button" onClick={onAddLocale}>
          Add locale
        </button>
      </div>

      <div className="scroll">
        <table>
          <thead>
            <tr>
              <th>Module</th>
              <th>Key</th>
              <th>Source</th>
              <th>Translation</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <TranslationRow
                key={`${row.module}:${row.key}:${row.item}`}
                row={row}
                warnings={warningsByRow.get(`${row.module}:${row.key}`) ?? []}
                onSave={save}
              />
            ))}
          </tbody>
        </table>
        {detail && rows.length === 0 && (
          <p className="empty">No rows match the current filters.</p>
        )}
      </div>
    </div>
  );
}

function Cards({ catalog }: { catalog: Catalog }) {
  const translated = catalog.locales.reduce((sum, l) => sum + l.translated, 0);
  const total = catalog.locales.reduce((sum, l) => sum + l.total, 0);
  const percent = total === 0 ? 100 : Math.round((100 * translated) / total);
  const warnings = catalog.locales.reduce((sum, l) => sum + l.warnings, 0);
  return (
    <div className="cards">
      <Card label="Locales" value={String(catalog.locales.length)} />
      <Card label="Modules" value={String(catalog.modules.length)} />
      <Card label="Coverage" value={`${percent}%`} sub={`${translated}/${total}`} />
      <Card label="Errors" value={String(catalog.errors.length)} tone={catalog.errors.length ? "warn" : "ok"} />
      <Card label="Warnings" value={String(warnings)} tone={warnings ? "warn" : "ok"} />
      <Card label="Unused keys" value={String(catalog.orphans.length)} tone={catalog.orphans.length ? "warn" : "ok"} />
    </div>
  );
}

function Card({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "ok" | "warn";
}) {
  return (
    <div className={`card${tone ? ` ${tone}` : ""}`}>
      <span className="value">{value}</span>
      <span className="label">{label}</span>
      {sub && <span className="sub">{sub}</span>}
    </div>
  );
}

function TranslationRow({
  row,
  warnings,
  onSave,
}: {
  row: Row;
  warnings: LocaleWarning[];
  onSave: (row: Row, text: string) => void;
}) {
  const [draft, setDraft] = useState(row.translation);

  useEffect(() => {
    setDraft(row.translation);
  }, [row.translation]);

  const commit = () => {
    if (draft !== row.translation) onSave(row, draft);
  };

  return (
    <tr data-status={row.status}>
      <td>{row.module}</td>
      <td>
        {row.key}
        {row.item && <span className="item"> [{row.item}]</span>}
        {warnings.length > 0 && (
          <span className="warn-flag" title={warnings.map((w) => w.message).join("\n")}>
            ⚠ {warnings.length}
          </span>
        )}
      </td>
      <td className="text source">{row.source_text}</td>
      <td className="text">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onBlur={commit}
          onKeyDown={(event) => {
            if (event.key === "Enter") event.currentTarget.blur();
          }}
        />
      </td>
      <td>
        <span className={`badge ${row.status}`}>
          {STATUS_LABEL[row.status] ?? row.status}
        </span>
      </td>
    </tr>
  );
}
