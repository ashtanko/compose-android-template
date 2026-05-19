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

# Run linting and static analysis
./gradlew detekt

# Format code
./gradlew spotlessApply
```

## 🏗️ Project Architecture

The project follows a modular layout backed by Gradle convention plugins:

```
├── app/                    # Main Android application (Compose + Navigation 3)
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

Convention plugins under `build-logic/convention` (e.g. `androidlab.android.application`, `androidlab.android.library.compose`, `androidlab.hilt`, `androidlab.android.room`, `androidlab.android.lint`) keep per-module `build.gradle.kts` files small and consistent.

## 🛠️ Technology Stack

### Core Technologies
- **Kotlin 2.3.21** — with Strong Skipping support.
- **Android Gradle Plugin 9.2.1** — latest build system features.
- **Jetpack Compose** — Compose BOM `2026.05.00`, Material 3, Material 3 Adaptive.
- **Navigation 3** (`1.1.1`) alongside `androidx.navigation:navigation-compose` (`2.9.8`).
- **Kotlin Coroutines 1.11.x** and **kotlinx.serialization 1.11.x**.

### Architecture & Dependencies
- **Hilt 2.59.2** — dependency injection (+ `hilt-navigation-compose`).
- **Room 2.8.x** — local persistence (via KSP).
- **Retrofit 3.0.0 + OkHttp 5.3.x** — type-safe networking with `kotlinx-serialization` converter.
- **Sandwich 2.2.x** — Retrofit response wrapping.
- **Paging 3** — smooth list loading.
- **Coil 2.7** — image loading optimized for Compose.
- **kotlinx-datetime** and **kotlinx.collections.immutable**.

### Testing & Quality
- **JUnit 5 (6.0.x)** — modern unit testing.
- **Roborazzi 1.60.x** — screenshot / golden-image testing.
- **Compose Guard** — Compose compiler stability metrics.
- **Kover 0.9.x + JaCoCo 0.8.x** — coverage reports.
- **Detekt 1.23.x + KtLint + Spotless 8.4.x** — static analysis & formatting.
- **Dependency Guard** — transitive dependency change detection.
- **MockK + Mockito + Turbine + Truth + AssertJ** — testing toolkit.
- **Robolectric** & **Espresso** — JVM- and device-side instrumentation.

## 📱 Features

- **Adaptive Layouts** — foldables and tablets via Material 3 Adaptive.
- **Edge-to-Edge** — modern UI implementation by default.
- **Baseline Profiles** — generated via `:benchmarks` for faster startup and smoother frames.
- **Screenshot Testing** — automated UI regression with Roborazzi + the Compose screenshot plugin.
- **Dependency Guard** — locks transitive dependency surface across builds.
- **Signing-ready** — release `signingConfig` resolves keystore credentials from env vars on CI (`SIGNING_STORE_PASSWORD`, `SIGNING_KEY_ALIAS`, `SIGNING_KEY_PASSWORD`) or `secrets.defaults.properties` locally.

## 🧪 Testing

```bash
# Run unit tests (JUnit 5)
./gradlew test

# Screenshot tests (Roborazzi)
./gradlew recordRoborazziDebug   # record new baselines
./gradlew verifyRoborazziDebug   # compare against baselines

# Coverage
./gradlew koverHtmlReport

# Instrumentation tests
./gradlew :app:connectedDebugAndroidTest

# Macrobenchmarks & baseline profile
./gradlew :benchmarks:connectedDebugAndroidTest
./gradlew :app:generateBaselineProfile
```

## 🚀 Available Commands (Makefile)

The `Makefile` wraps common Gradle invocations:

- `make` / `make default` — `build`, `test`, `lint`, `detekt`, plus `updateDebugScreenshotTest` and `validateDebugScreenshotTest`.
- `make check` — run Detekt.
- `make ktlint` — run KtLint check.
- `make spotless` — run Spotless apply + check.
- `make test` — JVM unit tests.
- `make android-test` — `:app:connectedDebugAndroidTest`.
- `make screenshot` — update + validate screenshot tests.
- `make robo` — clear → record → compare → verify Roborazzi screenshots.
- `make kover` — generate Kover HTML coverage report.
- `make jacoco` — copy the JaCoCo HTML report to `jacocoReport/`.
- `make guard-baseline` — refresh Dependency Guard baselines.
- `make benchmark` — run macrobenchmarks.
- `make baseline-profile` — generate baseline profile for `:app`.
- `make lines` / `make cloc` — Kotlin LoC stats.

## 📋 Requirements

- **Android Studio** — Ladybug or newer.
- **JDK 21** — required for the build system (set as Kotlin/Java toolchain).
- **Android SDK** — `compileSdk` / `targetSdk`: **37**, `minSdk`: **24**.
- **Gradle** — uses the wrapper (`./gradlew`); AGP 9.2.x.

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch.
3. Ensure all CI checks pass.
4. Submit a pull request.

## 📄 License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.
