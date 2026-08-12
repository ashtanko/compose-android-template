# Localization web wizard

A development-only web tool for viewing and editing this repository's Android
translations. It is never packaged into the app and never runs in CI. It reuses
the `scripts/localization` package for every read and write, so edits go through
the same validated, minimal-diff path as the command line.

## What it does

- Shows coverage per locale and per module, plus errors, quality warnings, and
  unused keys.
- Lets you edit a translation inline; saving writes `strings.xml` with a minimal
  diff (header, comments, order, and indentation preserved).
- Scaffolds a new locale across every owning module (`Add locale`).
- Adds a new default string to a module (`Add string`).

## Running it

Two processes during development: the Python backend and the Vite dev server.

1. Install the backend extras (once), then start the API from the repository root:

   ```bash
   python3 -m pip install -r tools/localization-web/requirements.txt
   make localization-serve            # http://localhost:8080
   ```

2. Install and start the frontend (proxies `/api` to the backend):

   ```bash
   cd tools/localization-web
   npm install
   npm run dev                        # http://localhost:5173
   ```

### Single-server option

Build the frontend once and let the backend serve it as static files:

```bash
cd tools/localization-web && npm run build
make localization-serve              # serves the UI and API on http://localhost:8080
```

## Notes

- The backend binds to `127.0.0.1` by default and edits files under the
  repository root it is launched from.
- Plural and array editing is not yet exposed in the UI; use the CLI for those.
