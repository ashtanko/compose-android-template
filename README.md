# Android Compose Template 🚀

[![Use this template](https://img.shields.io/badge/from-kotlin--android--template-brightgreen?logo=dropbox)](https://github.com/ashtanko/compose-android-template/generate) 
[![Android CI](https://github.com/ashtanko/compose-android-template/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ashtanko/compose-android-template/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/cortinico/kotlin-android-template.svg)](LICENSE)
[![Language](https://img.shields.io/github/languages/top/cortinico/kotlin-android-template?color=blue&logo=kotlin)](https://kotlinlang.org/)

A modern, production-ready Android template built with **Jetpack Compose** and **Kotlin**. This template provides a solid foundation for building Android applications with best practices, comprehensive testing, and CI/CD already configured.

## 🎯 Quick Start

### Using the Template

1. Click the **[Use this template](https://github.com/ashtanko/compose-android-template/generate)** button to create a new repository
2. Clone your new repository
3. Update the following files with your project details:
   - `buildSrc/src/main/kotlin/dev/shtanko/template/Configuration.kt` - Update version and SDK configurations
   - `app/src/main/AndroidManifest.xml` - Update package name and permissions
   - `library-android/src/main/AndroidManifest.xml` - Update package name
   - Rename package directories to match your project structure

### Building the Project

```bash
# Build the project
./gradlew build

# Run tests
./gradlew test

# Run linting and code analysis
./gradlew detekt

# Format code
./gradlew spotlessApply
```

## 🏗️ Project Architecture

This template follows a modular architecture with the following structure:

```
├── app/                    # Main Android application module
├── library-android/        # Android library module
├── library-kotlin/         # Kotlin-only library module
├── buildSrc/              # Build configuration and dependencies
├── gradle/                # Version catalogs and build scripts
├── config/                # Static analysis configuration
└── .github/workflows/     # CI/CD workflows
```

### Module Structure

- **app**: Main Android application with Compose UI
- **library-android**: Reusable Android components and utilities
- **library-kotlin**: Platform-agnostic business logic and data models

## 🛠️ Technology Stack

### Core Technologies
- **Kotlin** - Primary programming language
- **Jetpack Compose** - Modern UI toolkit
- **Material 3** - Design system
- **Android Gradle Plugin 8.10.1** - Build system
- **Gradle Kotlin DSL** - Build configuration

### Architecture & Dependencies
- **Hilt** - Dependency injection
- **Room** - Local database
- **Retrofit + OkHttp** - Network communication
- **Kotlinx Serialization** - JSON serialization
- **Paging 3** - Pagination support
- **Navigation Compose** - Navigation
- **WorkManager** - Background tasks
- **Coil** - Image loading

### Testing Framework
- **JUnit 5** - Unit testing
- **Espresso** - UI testing
- **Robolectric** - Android framework testing
- **Mockito/MockK** - Mocking
- **Turbine** - Flow testing
- **Roborazzi** - Screenshot testing

### Code Quality & Analysis
- **Detekt** - Static code analysis
- **KtLint** - Code formatting
- **Spotless** - Code formatting
- **SonarQube** - Code quality analysis
- **Kover** - Code coverage
- **Jacoco** - Coverage reporting

## 📱 Features

### UI/UX
- **Material 3 Design System** - Modern, adaptive design
- **Dark/Light Theme Support** - Complete theming system
- **Responsive Layout** - Adaptive to different screen sizes
- **Accessibility Support** - WCAG compliance ready
- **Splash Screen** - Modern splash screen implementation

### Development Experience
- **Hot Reload** - Fast development with Compose
- **Type Safety** - Full Kotlin type safety
- **Auto-completion** - Enhanced IDE support
- **Debug Tools** - Comprehensive debugging utilities

### Performance
- **Baseline Profiles** - Performance optimization
- **Benchmarking** - Performance measurement tools
- **Memory Leak Detection** - Built-in memory analysis
- **ProGuard/R8** - Code optimization and obfuscation

## 🔧 Configuration

### Build Configuration

The project uses centralized dependency management through `gradle/libs.versions.toml`:

```kotlin
// Example dependency usage
implementation(libs.androidx.compose.ui)
implementation(libs.androidx.navigation.compose)
implementation(libs.hilt.android)
```

### Static Analysis

Configure code quality tools in their respective config files:

- **Detekt**: `config/detekt/detekt.yml`
- **KtLint**: Configured via Gradle plugin
- **Spotless**: Configured in `build.gradle.kts`

### CI/CD Pipeline

The template includes GitHub Actions workflows for:

- **Build & Test**: Automated testing on every PR
- **Code Quality**: Static analysis and formatting checks
- **Publishing**: Automated library publishing (configurable)

## 🧪 Testing

### Unit Tests
```bash
# Run all unit tests
./gradlew testDebugUnitTest

# Run tests with coverage
./gradlew koverHtmlReport
```

### UI Tests
```bash
# Run Espresso tests
./gradlew connectedAndroidTest

# Run screenshot tests
./gradlew updateDebugScreenshotTest
./gradlew validateDebugScreenshotTest
```

### Code Quality Checks
```bash
# Run static analysis
./gradlew detekt

# Check code formatting
./gradlew ktlintCheck

# Apply code formatting
./gradlew spotlessApply
```

## 📦 Publishing

### Library Publishing

The template is configured for publishing to Maven Central. Configure the following secrets:

| Secret | Description |
|--------|-------------|
| `ORG_GRADLE_PROJECT_NEXUS_USERNAME` | Sonatype username |
| `ORG_GRADLE_PROJECT_NEXUS_PASSWORD` | Sonatype password |
| `ORG_GRADLE_PROJECT_SIGNING_KEY` | GPG private key |
| `ORG_GRADLE_PROJECT_SIGNING_PWD` | GPG passphrase |

### Publishing Workflows

- **Snapshot Publishing**: Automatic on merge to main
- **Release Publishing**: Triggered by version tags

## 🚀 Available Commands

Use the provided Makefile for common tasks:

```bash
# Build and test everything
make default

# Run code quality checks
make check

# Format code
make spotless

# Generate coverage report
make kover

# Run screenshot tests
make screenshot
```

## 📋 Requirements

- **Android Studio** - Latest stable version
- **JDK 17** - Java Development Kit
- **Android SDK** - API level 33+ (Android 13+)
- **Gradle** - 8.0+ (included via wrapper)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

### Development Guidelines

- Follow Kotlin coding conventions
- Write unit tests for new features
- Ensure all CI checks pass
- Update documentation as needed

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the excellent [kotlin-android-template](https://github.com/cortinico/kotlin-android-template)
- Uses modern Android development best practices
- Incorporates community-driven improvements

---

**Ready to build amazing Android apps?** 🎉 Start with this template and focus on what matters most - your app's features and user experience!