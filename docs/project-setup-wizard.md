# Project setup wizard

The setup wizard turns this repository into a configured Android project through either a guided
terminal flow or a local browser UI. Both surfaces use the same validation, capability resolver,
operation planner, transaction, and versioned JSON configuration.

## Start the wizard

```bash
# Guided terminal
./scripts/setup-project.sh

# Browser UI served only on 127.0.0.1
./scripts/setup-project.sh --ui

# Non-interactive preview
./scripts/setup-project.sh \
    --package com.example.myapp \
    --name "My App" \
    --preset standard \
    --remove-examples \
    --output ../my-app

# Apply after reviewing the preview
./scripts/setup-project.sh \
    --package com.example.myapp \
    --name "My App" \
    --preset standard \
    --remove-examples \
    --output ../my-app \
    --apply
```

Preview is always the default. Copy mode copies Git-tracked template files into an isolated
temporary directory, applies the full configuration, and publishes the destination only after the
transaction succeeds. It excludes Git history, ignored files, build output, IDE state, local
credentials, and signing material.

Use `--in-place` when the current clone is the intended target. A dirty worktree is refused unless
`--force` is explicit. The wizard snapshots non-ignored repository files so identity changes,
module removal, and dependency changes can be restored together if application fails.

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

Schema version 1 has this shape:

```json
{
  "schemaVersion": 1,
  "identity": {
    "packageName": "com.example.myapp",
    "projectName": "My App",
    "pluginAlias": "myapp",
    "author": "Example Author"
  },
  "output": {
    "mode": "copy",
    "path": "../my-app"
  },
  "starter": {
    "removeExamples": true
  },
  "capabilities": [
    "adaptive_ui",
    "coil",
    "coroutines",
    "hilt",
    "navigation",
    "networking",
    "room",
    "serialization",
    "test_tooling"
  ],
  "validation": {
    "format": false,
    "level": "none"
  }
}
```

Explicit CLI identity, output, starter, preset, capability, and validation options override values
loaded with `--config`.

## Validation and local UI security

`--format` runs Spotless after generation. `--verify narrow` assembles the app and runs its unit
tests; `--verify full` runs the repository's canonical `make verify` contract.

The browser UI has no CDN, analytics, external fonts, or package installation. Its temporary server:

- binds to an ephemeral `127.0.0.1` port;
- requires a random session token and same-origin requests;
- accepts bounded JSON requests only;
- rejects destinations inside the source template;
- applies only the exact digest returned by the latest preview;
- invokes allowlisted commands as argument arrays rather than shell strings.
