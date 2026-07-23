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
3. Run the rename script to replace template package names, applicationId, plugin aliases, folder structure, and (optionally) copyright headers with your own:

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

   After applying, run `./gradlew spotlessApply` then `./gradlew clean assembleDebug` to verify.

4. Update SDK and library versions in `gradle/libs.versions.toml` as needed (single source of truth for dependencies and plugin versions).

### Building the Project

```bash
# Build the project
./gradlew assembleDebug

# Run unit tests
./gradlew test

# Run the same host-side verification used by pull requests
make verify

# Run linting and static analysis
./gradlew detekt

# Run only Compose-specific static analysis
./gradlew detektCompose

# Apply fixes exposed as safe Detekt auto-corrections
./gradlew detektAutoCorrect

# Format code
./gradlew spotlessApply
```

### Local configuration

For local release signing, use an untracked `key.properties` file with `storeFile`,
`storePassword`, `keyAlias`, and `keyPassword`. CI keeps the existing
`SIGNING_STORE_PASSWORD`, `SIGNING_KEY_ALIAS`, and `SIGNING_KEY_PASSWORD` environment-variable
contract.

## 🏗️ Project Architecture

The project follows a modular layout backed by Gradle convention plugins:

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for layer responsibilities, dependency direction, UI-state
rules, and the complete posts demo walkthrough.

```
├── .agents/                # Shared coding-agent references, skills, and hooks
├── AGENTS.md               # Canonical coding-agent instructions
├── app/                    # Main Android application (Compose + Navigation 3)
├── core/                   # Shared application foundations, such as navigation
├── feature/                # Feature-focused modules
│   └── posts/              # Clean Architecture demo
│       ├── domain/         # model/, repository/, result/, usecase/
│       ├── data/           # di/, local/, remote/, mapper/, repository/
│       └── presentation/   # di/, ui/, ui/model/, ui/components/
├── library-android/        # Android-specific library module
├── library-kotlin/         # Pure Kotlin library module (business logic)
├── benchmarks/             # Macrobenchmark + baseline profile generator
├── build-logic/            # Shared Gradle convention plugins (includeBuild)
├── buildSrc/               # Project-wide build configuration
├── gradle/                 # Version catalog (libs.versions.toml)
├── config/                 # Detekt / KtLint / static-analysis configs
├── spotless/               # Spotless copyright header template
└── scripts/                # Helper scripts (e.g. rename-template.sh)
```

Convention plugins under `build-logic/convention` (e.g. `androidlab.android.application.compose`, `androidlab.android.library.compose`, `androidlab.android.feature`, `androidlab.android.junit5`, `androidlab.android.compose.screenshot`, `androidlab.android.roborazzi`, `androidlab.android.benchmark`, `androidlab.hilt`, `androidlab.android.room`, `androidlab.android.lint`, and the selective `androidlab.kotlin.explicit-visibility`) keep per-module `build.gradle.kts` files small and consistent.

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
- **Roborazzi** — screenshot / golden-image testing.
- **Compose Guard** — Compose compiler stability metrics.
- **Kover + JaCoCo** — coverage reports.
- **Detekt + Compose Rules + KtLint + Spotless** — Kotlin and Compose-specific static analysis,
  selective explicit-visibility enforcement for feature/layer modules, and formatting.
- **Dependency Guard** — transitive dependency change detection.
- **MockK + Mockito + Turbine + Truth + AssertJ** — testing toolkit.
- **Robolectric** & **Espresso** — JVM- and device-side instrumentation.

## 📱 Features

- **Posts architecture demo** — Retrofit pagination, in-memory cache fallback, DTO/domain/UI
  mapping, Hilt, sealed UI state, retry, and incremental loading.
- **Adaptive Layouts** — foldables and tablets via Material 3 Adaptive.
- **Edge-to-Edge** — modern UI implementation by default.
- **Baseline Profiles** — generated via `:benchmarks` for faster startup and smoother frames.
- **Screenshot Testing** — automated UI regression with Roborazzi + the Compose screenshot plugin.
- **Dependency Guard** — locks transitive dependency surface across builds.
- **Signing-ready** — release `signingConfig` resolves keystore credentials from env vars on CI (`SIGNING_STORE_PASSWORD`, `SIGNING_KEY_ALIAS`, `SIGNING_KEY_PASSWORD`) or an untracked `key.properties` file locally.

## 🧪 Testing

```bash
# Run unit tests (JUnit 5)
./gradlew test

# Compose Preview screenshot tests
./gradlew validateDebugScreenshotTest  # compare against approved references
./gradlew updateDebugScreenshotTest    # intentionally update references

# Screenshot tests (Roborazzi)
./gradlew recordRoborazziDebug   # record new baselines
./gradlew verifyRoborazziDebug   # compare against baselines

# Coverage
./gradlew :app:koverHtmlReport

# Instrumentation tests
./gradlew :app:connectedDebugAndroidTest

# Macrobenchmarks & baseline profile
./gradlew :benchmarks:connectedBenchmarkReleaseAndroidTest
./gradlew :app:generateBaselineProfile
```

## 🚀 Available Commands (Makefile)

The `Makefile` wraps common Gradle invocations:

- `make` / `make help` — list available targets without changing the project.
- `make docs-check` — validate documentation links and project facts.
- `make build` / `make install` — assemble or install the debug app.
- `make test` — run unit tests.
- `make check` — run lint, Detekt, Spotless, and Dependency Guard checks.
- `make verify` — run the canonical non-mutating host checks used by pull requests.
- `make template-check` — validate the rename dry run and generated module structure.
- `make format-check` / `make format` — check or apply formatting.
- `make device-test` — run debug instrumentation tests on connected devices.
- `make screenshot-test` / `make screenshot-record` — verify or update Compose screenshot baselines.
- `make roborazzi-test` / `make roborazzi-record` — verify or update Roborazzi baselines.
- `make coverage` — generate the app Kover HTML coverage report.
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
canonical source.

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch.
3. Ensure all CI checks pass.
4. Submit a pull request.

## 📄 License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.
