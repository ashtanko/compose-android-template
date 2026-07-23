# Commands and validation

Run commands from the repository root with the Gradle wrapper. JDK 21 is required.

## Focused commands

| Change | Start with |
| --- | --- |
| Documentation only | `make docs-check` |
| Shell script | `bash -n path/to/script.sh` plus a safe dry run when supported |
| Pure Kotlin module | `./gradlew :module:test` |
| Android module | `./gradlew :module:testDebugUnitTest` |
| App unit behavior | `./gradlew :app:testDebugUnitTest` |
| Formatting | `./gradlew spotlessCheck` |
| Static analysis | `./gradlew detekt` |
| Android lint | `./gradlew lint` or `./gradlew :module:lintDebug` |
| Screenshot verification | `./gradlew validateDebugScreenshotTest` and/or `./gradlew verifyRoborazziDebug` |
| Instrumentation | `./gradlew :app:connectedDebugAndroidTest` with a device or emulator available |
| Macrobenchmark | `./gradlew :benchmarks:connectedBenchmarkReleaseAndroidTest` |

Replace `:module` with the actual Gradle path, for example `:core:navigation`. Use `--tests "fully.qualified.ClassName"` to narrow a unit-test task when iterating.

`make docs-check` validates local Markdown links, documented Make targets, module references,
the canonical agent entrypoint, and version-policy consistency without starting Gradle.

## Broader verification

For a cross-module or pre-PR change, use the non-mutating verification target:

```bash
make verify
```

It assembles debug artifacts and runs unit tests, lint, Detekt, Spotless, and Dependency Guard without requiring release signing.

Add screenshot verification when UI output changed. Routine Make targets are non-mutating; use `make screenshot-record` or `make roborazzi-record` only when updating visual baselines is intentional.

## Mutating commands

- Use `./gradlew spotlessApply` only when formatting changes are in scope; review its diff afterward.
- Use `./gradlew :app:dependencyGuardBaseline` only for an intentional dependency-surface change.
- Use `./gradlew :app:generateBaselineProfile` only for intentional baseline-profile work with the required device setup.
- Avoid `clean` for routine verification. Use it when diagnosing stale outputs or after a template rename.

## Module generation

Use `bash scripts/add-module.sh` with explicit flags for repeatable, non-interactive module creation. Follow [the module skill](../skills/add-android-module/SKILL.md) and inspect all generated files before keeping them.
