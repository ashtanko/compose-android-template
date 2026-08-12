# Project setup wizard

The setup wizard turns this repository into a configured Android project through a guided terminal
flow, a local browser UI, or a deployable download-only browser service. All surfaces use the same
validation, capability resolver, operation planner, transaction, archive builder, and versioned
JSON configuration.

## Start the wizard

```bash
# Guided terminal
./scripts/setup-project.sh

# Browser UI served only on 127.0.0.1
./scripts/setup-project.sh --ui

# Non-interactive ZIP preview
./scripts/setup-project.sh \
    --package com.example.myapp \
    --name "My App" \
    --preset standard \
    --remove-examples \
    --ai-free \
    --archive ../my-app.zip

# Create the archive after reviewing the preview
./scripts/setup-project.sh \
    --package com.example.myapp \
    --name "My App" \
    --preset standard \
    --remove-examples \
    --ai-free \
    --archive ../my-app.zip \
    --apply
```

Preview is always the default. Archive mode copies Git-tracked template files into an isolated
temporary directory, applies the full configuration, and creates a deterministic ZIP with a single
project root. It preserves executable scripts and excludes Git history, ignored files, build
output, IDE state, local credentials, and signing material.

Use `--output ../my-app` to publish a directory copy, or `--in-place` when the current clone is the
intended target. A dirty worktree is refused unless `--force` is explicit. The wizard snapshots
non-ignored repository files so identity changes, module removal, and dependency changes can be
restored together if application fails.

## Configuration coverage

The UI inventories configuration surfaces as **editable**, **derived**, **inherited**, or
**manual**. These labels describe the actual setup boundary; the wizard does not expose every
Gradle property or version-catalog entry.

| Disposition | Configuration surface |
| --- | --- |
| Editable | Gradle project name, Kotlin/Java code package, application ID, launcher display name, convention-plugin alias, optional author, app version, Android SDK levels, retained-example backend URL, starter/capability selection, output, formatting, and verification |
| Derived | Module topology and active dependency/plugin declarations, based on the starter choice, selected capabilities, and their prerequisites |
| Inherited | Repository JVM target, dependency and plugin versions, Gradle memory/cache/parallelism settings, build types, shrinking, packaging, and inactive client defaults |
| Manual | Signing and CI credentials, launcher artwork, theme assets, locales, and translations |

The project identity fields have separate purposes:

- `packageName` is the Kotlin/Java code package rewritten across source and module paths.
- `projectName` is the Gradle root-project name.
- `applicationId` is the installed-app and Play identity. It defaults to `packageName`, but can
  differ from the source package.
- `displayName` is the launcher label. It defaults to `projectName`, but can differ from the Gradle
  project name.

`projectSettings` makes `versionCode`, `versionName`, `compileSdk`, `minSdk`, `targetSdk`, and
`benchmarkMinSdk` editable. The UI also displays `jvmTarget`, but it is fixed to the repository's
JDK/CI contract and has no CLI override. Change that contract as a coordinated template migration,
not as a generated-project option.

`postsBackendUrl` is editable only while the example modules are retained. It must be an absolute
HTTPS URL with a trailing slash and cannot contain credentials, a query, or a fragment. When
examples are removed, the resolved setting is `null`.

The wizard never asks for or writes signing secrets. Generated projects retain the documented
`key.properties` and `SIGNING_*` environment-variable contract. Dependency versions, custom build
types, Gradle tuning, and application assets also remain template-managed or manual follow-up work.

### CLI flags for editable values

| Configuration | CLI flag |
| --- | --- |
| Code package | `--package` |
| Gradle project name | `--name` |
| Application ID | `--application-id` |
| Launcher display name | `--display-name` |
| Convention-plugin alias | `--plugin-alias` |
| Author | `--author` |
| Version code and name | `--version-code`, `--version-name` |
| Android SDK levels | `--compile-sdk`, `--min-sdk`, `--target-sdk`, `--benchmark-min-sdk` |
| Retained posts-example backend | `--posts-backend-url` |
| Starter content | `--remove-examples` or `--keep-examples`; `--ai-free` or `--include-ai` |
| Curated dependencies | `--preset`; repeat `--capability` for additions |
| Output | `--archive`, `--output`, or `--in-place` |
| Final checks | `--format`, `--verify none|narrow|full` |

For example, code can remain under `com.example.myapp` while the installed app uses a different ID
and product-facing name:

```bash
./scripts/setup-project.sh \
    --package com.example.myapp \
    --name "My Android Workspace" \
    --application-id com.example.product \
    --display-name "My Product" \
    --version-code 42 \
    --version-name 4.2.0 \
    --compile-sdk 37 \
    --min-sdk 24 \
    --target-sdk 37 \
    --benchmark-min-sdk 28 \
    --keep-examples \
    --posts-backend-url https://api.example.com/ \
    --archive ../my-product.zip
```

## Presets and capabilities

| Preset | Included configuration |
| --- | --- |
| `minimal` | Android, Kotlin, Compose, Material, lifecycle, and core test/debug foundations |
| `standard` | Minimal plus Navigation 3, coroutines, serialization, Hilt, networking, Room, Coil, adaptive UI, and extended tests |
| `full` | Every supported runtime and tooling capability |
| `custom` | Only individually selected capability groups and their prerequisites |

The initial capability registry contains:

- Architecture: Navigation 3, coroutines, Kotlin serialization, and Hilt.
- Data: Retrofit/OkHttp networking, Room, and Paging.
- UI: Coil, adaptive/window APIs, Google Fonts, and extended Material icons.
- Platform: permission helpers and the generative AI client.
- Tooling: extended tests, screenshot tests, coverage, and baseline profiles.

Repeat `--capability <id>` to add groups to a preset. The wizard automatically enables prerequisites
and shows why they were added. Retaining the repository examples also retains their required
navigation, DI, networking, serialization, adaptive UI, and test stack.

Select **AI-free project** in the browser or pass `--ai-free` to exclude coding-agent guidance,
Claude skill links, and the Google generative-AI client from the configured project. This option
wins over the `full` preset or an explicitly requested `generative_ai` capability.

When `--remove-examples` is selected, the home, posts, database, Android sample library, and Kotlin
sample library modules are removed. The app receives a resource-backed Compose starter screen.
`core/designsystem` stays; `core/navigation` and `benchmarks` stay only when their capabilities are
selected.

Version-catalog and convention-plugin declarations remain available as the template's capability
registry. Unselected dependencies and plugins are removed from active generated-module build
files, so they do not enter generated project classpaths.

## Reproducible configuration

Export the resolved configuration from either UI or CLI:

```bash
./scripts/setup-project.sh \
    --package com.example.myapp \
    --name "My App" \
    --preset standard \
    --remove-examples \
    --output ../my-app \
    --export-config project-setup.json

./scripts/setup-project.sh --config project-setup.json
./scripts/setup-project.sh --config project-setup.json --apply
```

Schema version 3 has this shape. Exports contain fully resolved identity and project settings:

```json
{
  "schemaVersion": 3,
  "identity": {
    "packageName": "com.example.myapp",
    "projectName": "My Android Workspace",
    "applicationId": "com.example.product",
    "displayName": "My Product",
    "pluginAlias": "myapp",
    "author": "Example Author"
  },
  "output": {
    "mode": "archive",
    "path": null
  },
  "starter": {
    "removeExamples": false,
    "aiFree": true
  },
  "projectSettings": {
    "versionCode": 42,
    "versionName": "4.2.0",
    "compileSdk": 37,
    "minSdk": 24,
    "targetSdk": 37,
    "benchmarkMinSdk": 28,
    "jvmTarget": 21,
    "postsBackendUrl": "https://api.example.com/"
  },
  "capabilities": [
    "adaptive_ui",
    "coil",
    "coroutines",
    "hilt",
    "navigation",
    "networking",
    "room",
    "screenshots",
    "serialization",
    "test_tooling"
  ],
  "validation": {
    "format": false,
    "level": "none"
  }
}
```

Schema versions 1 and 2 remain importable. Migration derives `applicationId` from `packageName` and
`displayName` from `projectName`; missing project settings are read from the current source template
when the plan is resolved. Version 1 imports also default `aiFree` to `false`. Exports always use
schema version 3.

Explicit CLI identity, project-setting, output, starter, preset, capability, and validation options
override values loaded with `--config`. There is intentionally no `--jvm-target` flag.

## Deploy the download-only wizard

The included container runs the public server on `0.0.0.0:$PORT`:

```bash
docker build -t compose-project-wizard .
docker run --rm -p 8000:8000 -e PORT=8000 compose-project-wizard
```

Deploy that image on a container platform and terminate TLS at the platform or reverse proxy.
Public mode exposes preview and ZIP download only. It never accepts destination paths, formatting
commands, verification commands, or in-place application. The platform should set request time and
memory limits appropriate for the template archive size.

## Validation and browser security

`--format` runs Spotless after generation. `--verify narrow` assembles the app and runs its unit
tests; `--verify full` runs the repository's canonical `make verify` contract. Archive mode always
uses structural checks only so a public request cannot start Gradle or arbitrary host work.

The browser UI has no CDN, analytics, external fonts, or package installation. Local mode:

- binds to an ephemeral `127.0.0.1` port;
- requires a random session token and same-origin requests;
- accepts bounded JSON requests only;
- rejects destinations inside the source template;
- applies only the exact digest returned by the latest preview;
- invokes allowlisted commands as argument arrays rather than shell strings.

Public mode additionally:

- disables the filesystem apply endpoint;
- rejects every non-archive output configuration and redacts host filesystem paths;
- accepts archive generation only for the exact preview digest and current source state;
- copies only Git-tracked files or entries in the exact
  `scripts/setup_wizard/source-manifest.txt` container inventory, and fails closed when neither
  inventory is available;
- rejects cross-origin browser requests and oversized JSON bodies;
- caps concurrent planning and archive work before scanning the source, and returns a retryable
  busy response.
