// Typed client for the localization wizard backend (see scripts/localization/web.py).

export interface LocaleSummary {
  tag: string;
  translated: number;
  total: number;
  percent: number;
  warnings: number;
}

export interface Orphan {
  module: string;
  kind: string;
  name: string;
}

export interface Catalog {
  generated_at: string;
  modules: string[];
  locales: LocaleSummary[];
  errors: string[];
  orphans: Orphan[];
}

export interface Row {
  locale: string;
  module: string;
  resource_type: string;
  key: string;
  item: string;
  source_text: string;
  translation: string;
  status: string;
  source_file: string;
  translation_file: string;
}

export interface LocaleWarning {
  module: string;
  category: string;
  message: string;
}

export interface LocaleDetail {
  tag: string;
  translated: number;
  total: number;
  rows: Row[];
  warnings: LocaleWarning[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    let detail: unknown;
    try {
      detail = (await response.json()).detail;
    } catch {
      detail = response.statusText;
    }
    throw new Error(
      Array.isArray(detail) ? detail.join("; ") : String(detail),
    );
  }
  return (await response.json()) as T;
}

export function getCatalog(): Promise<Catalog> {
  return request<Catalog>("/api/catalog");
}

export function getLocale(tag: string): Promise<LocaleDetail> {
  return request<LocaleDetail>(`/api/locales/${encodeURIComponent(tag)}`);
}

export function setTranslation(body: {
  locale: string;
  module: string;
  name: string;
  text: string;
}): Promise<{ action: string; file: string }> {
  return request("/api/translation", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function addLocale(body: {
  locale: string;
  fill: string;
}): Promise<{ created: string[]; skipped: string[] }> {
  return request("/api/locales", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function addString(body: {
  module: string;
  name: string;
  text: string;
}): Promise<{ file: string }> {
  return request("/api/strings", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
