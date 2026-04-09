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
3. Update project details in:
   - `gradle/libs.versions.toml` - Update SDK and library versions (Source of truth).
   - `app/src/main/AndroidManifest.xml` - Update package name and permissions.
   - `app/build.gradle.kts` - Update `applicationId`.

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

The project follows a modular, clean architecture approach:

```
├── app/                    # Main Android application module (Compose + Nav 3)
├── library-android/        # Android-specific library module
├── library-kotlin/         # Pure Kotlin library module (Business logic)
├── build-logic/            # Shared Gradle convention plugins
├── gradle/                 # Version catalogs (libs.versions.toml)
└── config/                 # Detekt, KtLint, and other tool configs
```

## 🛠️ Technology Stack

### Core Technologies
- **Kotlin 2.3.x** - With Strong Skipping mode support.
- **Jetpack Compose** - Modern declarative UI.
- **Material 3** - Adaptive design system.
- **Navigation 3** - The latest evolution of Android Navigation.
- **Android Gradle Plugin 9.1.x** - Latest build system features.

### Architecture & Dependencies
- **Hilt** - Dependency injection.
- **Room** - Local persistence with KSP.
- **Retrofit + OkHttp** - Type-safe networking.
- **Kotlinx Serialization** - JSON parsing.
- **Paging 3** - Smooth list loading.
- **Coil** - Image loading optimized for Compose.

### Testing & Quality
- **JUnit 5** - Modern unit testing.
- **Roborazzi** - Screen recording and screenshot testing.
- **Compose Guard** - Monitoring Compose compiler stability.
- **Kover & Jacoco** - Comprehensive code coverage reports.
- **Detekt & Spotless** - Strict code style and static analysis.

## 📱 Features

- **Adaptive Layouts**: Support for Foldables and Tablets using Material 3 Adaptive.
- **Edge-to-Edge**: Modern UI implementation by default.
- **Baseline Profiles**: Optimized startup and frame rates.
- **Screenshot Testing**: Automated UI regression testing with Roborazzi.
- **Dependency Guard**: Monitoring transitive dependency changes.

## 🧪 Testing

```bash
# Run unit tests
./gradlew test

# Screenshot Tests (Roborazzi)
./gradlew recordRoborazziDebug   # Record new baselines
./gradlew verifyRoborazziDebug   # Compare against baselines

# Coverage Report
./gradlew koverHtmlReport
```

## 🚀 Available Commands (Makefile)

The project includes a `Makefile` for developer convenience:

- `make default`: Full build, test, and lint cycle.
- `make check`: Run Detekt and KtLint.
- `make robo`: Run full Roborazzi screenshot suite (Record + Verify).
- `make guard-baseline`: Update Dependency Guard baselines.
- `make spotless`: Apply code formatting.

## 📋 Requirements

- **Android Studio** - Ladybug or newer.
- **JDK 21** - Required for the build system.
- **Android SDK** - Compile/Target: 37, Min: 24.
- **Gradle** - 9.3+ (included via wrapper).

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch.
3. Ensure all CI checks pass.
4. Submit a pull request.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
