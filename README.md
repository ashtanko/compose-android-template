# Android Compose Template 🚀

[![Use this template](https://img.shields.io/badge/from-ashtanko--template-brightgreen?logo=github)](https://github.com/ashtanko/compose-android-template/generate)
[![Android CI](https://github.com/ashtanko/compose-android-template/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ashtanko/compose-android-template/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/ashtanko/compose-android-template.svg)](LICENSE)
[![Language](https://img.shields.io/github/languages/top/ashtanko/compose-android-template?color=blue&logo=kotlin)](https://kotlinlang.org/)

A modern, production-ready Android template built with **Jetpack Compose**, **Navigation 3**, and **Kotlin**. This template provides a solid foundation for building Android applications with best practices, comprehensive testing, and CI/CD already configured.

## 🎯 Quick Start

### Using the Template

1. Click the **[Use this template](https://github.com/ashtanko/compose-android-template/generate)** button.
2. Clone your new repository.
3. Run the rename script to replace template package names, applicationId, plugin aliases, source
   and screenshot-reference paths, display names, retained helper tooling, and (optionally)
   copyright headers with your own. The script requires Python 3.8 or newer, validates all
   destinations before writing, and rolls back changes if an operation fails:

   ```bash
   # preview first
   ./scripts/rename-template.sh \
       --package com.example.myapp \
       --name "My Awesome App" \
       --author "Your Name" \
       --dry-run

   # apply
   ./scripts/rename-template.sh \
       --package com.example.myapp \
       --name "My Awesome App" \
       --author "Your Name"
   ```

   Or via Gradle (same flags, `-P`-style):

   ```bash
   ./gradlew renameProject \
       -Ppackage=com.example.myapp \
       -Pname="My Awesome App" \
       -Pauthor="Your Name" \
       -PdryRun=true   # drop this to apply
   ```

   After applying, confirm the rename is complete with `./scripts/validate-rename.sh` (or
   `make rename-validate`). It fails if any original template identity, package folder, or plugin
   accessor remains. Then run `./gradlew spotlessApply` and `make verify`. Formatting is a separate
   step because package changes can alter Kotlin import ordering and the Gradle `renameProject`
   task cannot safely start a nested Gradle build.

4. Update SDK and library versions in `gradle/libs.versions.toml` as needed (single source of truth for dependencies and plugin versions).

### Building the Project

```bash
# Build the project
./gradlew assembleDebug

# Run unit tests
./gradlew test

# Run the same host-side verification used by pull requests
make verify

# Scan tracked files for credentials and sensitive release files
make secrets-check

# Run linting and static analysis
./gradlew detekt

# Run only Compose-specific static analysis
./gradlew detektCompose

# Apply fixes exposed as safe Detekt auto-corrections
./gradlew detektAutoCorrect

# Check translation completeness and formatter compatibility
make localization-check

# Format code
./gradlew spotlessApply
```

### Local configuration

Release builds use an untracked `key.properties` file locally and protected environment secrets in
GitHub Actions. See [`RELEASING.md`](RELEASING.md) for the copy-ready local file, GitHub secret
commands, interactive upload-key generator, protected-environment setup, and release workflow.

### Secret leak safeguards

Enable the repository-owned pre-commit hook once per clone:

```bash
git config core.hooksPath .agents/hooks
```

The hook checks staged Git blobs without reading ignored local credentials. A lightweight,
read-only GitHub Actions workflow repeats the check for every pull request, including
documentation-only changes. After its first run, make **Reject committed secrets** a required
status check in the default branch ruleset.

Repository administrators should also enable GitHub Secret Protection and push protection under
**Settings → Security → Advanced Security** when available; native provider-aware scanning
complements the repository's intentionally small, high-confidence rule set.

If a real credential is ever committed, revoke or rotate it immediately. Removing it in a later
commit does not make the exposed value safe.

## 🏗️ Project Architecture

The project follows a modular layout backed by Gradle convention plugins:

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for layer responsibilities, dependency direction, UI-state
rules, and the complete posts demo walkthrough.

```
├── .agents/                # Shared coding-agent references, skills, and hooks
├── AGENTS.md               # Canonical coding-agent instructions
├── app/                    # Main Android application (Compose + Navigation 3)
├── core/                   # Shared production foundations and test utilities
├── feature/                # Feature-focused modules
│   └── posts/              # Clean Architecture demo
│       ├── domain/         # model/, repository/, result/, usecase/
│       ├── data/           # di/, local/, remote/, mapper/, repository/
│       └── presentation/   # di/, ui/, ui/model/, ui/components/
├── library-android/        # Android-specific library module
├── library-kotlin/         # Pure Kotlin library module (business logic)
├── benchmarks/             # Macrobenchmark + baseline profile generator
├── tests/e2e/              # Managed-device application journeys
├── build-logic/            # Shared Gradle convention plugins (includeBuild)
├── buildSrc/               # Project-wide build configuration
├── gradle/                 # Version catalog (libs.versions.toml)
├── config/                 # Detekt / KtLint / static-analysis configs
├── spotless/               # Spotless copyright header template
└── scripts/                # Helper scripts (e.g. rename-template.sh)
```

Convention plugins under `build-logic/convention` (e.g. `androidlab.android.application.compose`, `androidlab.android.library.compose`, `androidlab.android.feature`, `androidlab.android.junit5`, `androidlab.android.compose.screenshot`, `androidlab.android.benchmark`, `androidlab.hilt`, `androidlab.android.room`, `androidlab.android.lint`, and the selective `androidlab.kotlin.explicit-visibility`) keep per-module `build.gradle.kts` files small and consistent.

Kotlin packages mirror these directories. Single-module UI features use `ui`, `ui/model`, and
`ui/components`; reusable components shared by unrelated features live in `core/designsystem`.

### Adding modules

Use `scripts/add-module.sh` to create and register feature, core, Android library, or Kotlin/JVM
modules. Generated Android modules intentionally start without explicit library dependencies. Add
only dependencies required by the implementation, prefer `implementation`, and use `api` only when
a dependency type is intentionally part of the module's public contract.

## 🛠️ Technology Stack

Library, Android build-plugin, and Android SDK versions are defined in
[`gradle/libs.versions.toml`](gradle/libs.versions.toml). The catalog is the source of truth for
those values; the summary below intentionally avoids copying fast-changing version numbers.

### Core Technologies
- **Kotlin** — configured through the version catalog and shared toolchains.
- **Android Gradle Plugin** — Android build configuration.
- **Jetpack Compose** — Compose BOM, Material 3, and Material 3 Adaptive.
- **Navigation 3** alongside `androidx.navigation:navigation-compose`.
- **Kotlin Coroutines** and **kotlinx.serialization**.

### Architecture & Dependencies
- **Hilt** — dependency injection (+ `hilt-navigation-compose`).
- **Room** — local persistence (via KSP).
- **Retrofit + OkHttp** — type-safe networking with a `kotlinx-serialization` converter.
- **Sandwich** — Retrofit response wrapping.
- **Paging 3** — smooth list loading.
- **Coil** — image loading optimized for Compose.
- **kotlinx-datetime** and **kotlinx.collections.immutable**.
- **Clean Architecture + MVVM** — an end-to-end paginated posts feature with enforced domain,
  data, and presentation module boundaries.

### Testing & Quality
- **JUnit 5** — modern unit testing.
- **Compose Preview Screenshot Testing** — host-side adaptive visual regression testing.
- **Compose Guard** — Compose compiler stability metrics.
- **JaCoCo** — coverage reports and JVM business-logic thresholds.
- **Detekt + Compose Rules + KtLint + Spotless** — Kotlin and Compose-specific static analysis,
  selective explicit-visibility enforcement for feature/layer modules, and formatting.
- **Dependency Guard** — transitive dependency change detection.
- **MockK + Mockito + Turbine + Truth + AssertJ** — testing toolkit.
- **Robolectric, Compose Test, AndroidX Test, and UI Automator** — local UI, integration, and
  end-to-end testing.

## 📱 Features

- **Posts architecture demo** — Retrofit pagination, in-memory cache fallback, DTO/domain/UI
  mapping, Hilt, sealed UI state, retry, and incremental loading.
- **Adaptive Layouts** — foldables and tablets via Material 3 Adaptive.
- **Edge-to-Edge** — modern UI implementation by default.
- **Baseline Profiles** — generated via `:benchmarks` for faster startup and smoother frames.
- **Screenshot Testing** — automated adaptive UI regression with the Compose screenshot plugin.
- **Dependency Guard** — locks transitive dependency surface across builds.
- **Signing-ready** — local builds resolve keystore credentials from an untracked `key.properties` file, while CI reads env vars (`SIGNING_STORE_PASSWORD`, `SIGNING_KEY_ALIAS`, `SIGNING_KEY_PASSWORD`, `SIGNING_KEYSTORE_PATH`); a manually approved GitHub Actions workflow restores an upload key only on its ephemeral runner and retains the signed AAB plus R8 mapping.
- **Localization-ready** — English fallback resources, European Portuguese translations,
  generated per-app language configuration, pseudolocales, and translation validation/reporting.

See [`LOCALIZATION.md`](LOCALIZATION.md) for the resource strategy, translator workflow, and
validation matrix.

## 🧪 Testing

```bash
# Run unit tests (JUnit 5)
./gradlew test

# Run deterministic JVM integration tests
./gradlew integrationTest

# Compose Preview screenshot tests
./gradlew validateDebugScreenshotTest  # compare against approved references
./gradlew updateDebugScreenshotTest    # intentionally update references

# Coverage reports and JVM business-logic gate
./gradlew coverageReport
./gradlew coverageVerification

# Instrumentation and end-to-end tests on the managed CI phone/tablet group
./gradlew ciManagedDeviceTest

# Macrobenchmarks & baseline profile
# Run timing measurements on a stable, connected physical device.
./gradlew :benchmarks:connectedBenchmarkReleaseAndroidTest
# Generate profiles reproducibly with the managed device declared by :benchmarks.
./gradlew :app:generateBaselineProfile
```

## 🚀 Available Commands (Makefile)

The `Makefile` wraps common Gradle invocations:

- `make` / `make help` — list available targets without changing the project.
- `make docs-check` — validate documentation links and project facts.
- `make localization-check` — validate translated resources in every Android module.
- `make localization-report LOCALE=pt-PT FORMAT=csv` — export translation coverage.
- `make secrets-check` — reject tracked credentials and sensitive release files.
- `make build` / `make install` — assemble or install the debug app.
- `make test` — run unit tests.
- `make integration-test` — run JVM integration tests.
- `make check` — run lint, Detekt, Spotless, and Dependency Guard checks.
- `make verify` — run the canonical non-mutating host checks used by pull requests.
- `make template-check` — validate the rename dry run and generated module structure.
- `make rename-validate` — verify this project was fully renamed away from the template.
- `make format-check` / `make format` — check or apply formatting.
- `make device-test` — run debug instrumentation tests on connected devices.
- `make device-test-ci` / `make device-test-all` — run every instrumentation and end-to-end test
  on the CI or complete managed-device matrix.
- `make screenshot-test` / `make screenshot-record` — verify or update Compose screenshot baselines.
- `make coverage` / `make coverage-verify` — generate coverage reports or enforce JVM thresholds.
- `make dependency-guard` / `make dependency-guard-baseline` — verify or update dependency baselines.
- `make benchmark` — run `benchmarkRelease` macrobenchmarks.
- `make baseline-profile` — generate the app baseline profile.

Pass additional Gradle options with `GRADLE_ARGS`, for example:

```bash
make verify GRADLE_ARGS="--no-daemon --stacktrace"
```

## 📋 Requirements

- **Android Studio** — a release compatible with the AGP and SDK levels configured in
  [`gradle/libs.versions.toml`](gradle/libs.versions.toml).
- **JDK 21** — required for the build system (set as Kotlin/Java toolchain).
- **Android SDK** — install the compile SDK declared in the version catalog.
- **Gradle** — use the checked-in wrapper (`./gradlew`).

## 🤖 AI-assisted development

Coding agents should start with [`AGENTS.md`](AGENTS.md). The [`.agents` workspace](.agents/README.md)
contains progressively loaded architecture, decision, testing, security, performance, and validation
references, concrete Android/Kotlin implementation rules, reusable task skills, and an optional
pre-commit hook. `CLAUDE.md` remains a thin Claude Code adapter so repository guidance has one
canonical source. Complete features follow the
[`deliver-android-feature`](.agents/skills/deliver-android-feature/SKILL.md) workflow so acceptance
criteria, implementation, every required test layer, and CI evidence remain traceable.

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch.
3. Ensure all CI checks pass.
4. Submit a pull request.

## 📄 License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.
