# Commands and validation

Run commands from the repository root with the Gradle wrapper. JDK 21 is required.

## Focused commands

| Change | Start with |
| --- | --- |
| Documentation only | `make docs-check` |
| Template tooling | `make template-check` |
| Shell script | `bash -n path/to/script.sh` plus a safe dry run when supported |
| Pure Kotlin module | `./gradlew :module:test` |
| Android module | `./gradlew :module:testDebugUnitTest` |
| App unit behavior | `./gradlew :app:testDebugUnitTest` |
| Formatting | `./gradlew spotlessCheck` |
| Static analysis | `./gradlew detekt` |
| Compose-specific static analysis | `./gradlew detektCompose` |
| Android lint | `./gradlew lint` or `./gradlew :module:lintDebug` |
| Screenshot verification | `./gradlew validateDebugScreenshotTest` and/or `./gradlew verifyRoborazziDebug` |
| Instrumentation | `./gradlew :app:connectedDebugAndroidTest` with a device or emulator available |
| Macrobenchmark | `./gradlew :benchmarks:connectedBenchmarkReleaseAndroidTest` |

Replace `:module` with the actual Gradle path, for example `:core:navigation`. Use `--tests "fully.qualified.ClassName"` to narrow a unit-test task when iterating.

`make docs-check` validates local Markdown links, documented Make targets, module references,
the canonical agent entrypoint, and version-policy consistency without starting Gradle.

`./gradlew detekt` runs the standard and Compose rule sets across all Kotlin sources. In modules
that apply `androidlab.kotlin.explicit-visibility`, it also fails on eligible declarations without
an explicit visibility modifier.
`./gradlew detektCompose` is the faster production-source check for Compose rules only.
`./gradlew detektAutoCorrect` applies fixes only for rules that explicitly support auto-correction;
Compose API findings such as parameter order still require a code change.

## Broader verification

For a cross-module or pre-PR change, use the canonical non-mutating verification target:

```bash
make verify
```

It validates documentation and template tools, checks build logic, assembles debug artifacts, and
runs unit tests, lint, Detekt, Spotless, Dependency Guard, Compose screenshot validation, and
Roborazzi verification without requiring release signing. The host-side pull-request job invokes
this exact target; managed-device tests remain a separate environment-dependent CI job.

Routine verification never records baselines. Use `make screenshot-record`,
`make roborazzi-record`, or `make dependency-guard-baseline` only when the corresponding change is
intentional, then review every generated diff.

## Mutating commands

- Use `./gradlew spotlessApply` only when formatting changes are in scope; review its diff afterward.
- Use `./gradlew :app:dependencyGuardBaseline` only for an intentional dependency-surface change.
- Use `./gradlew :app:generateBaselineProfile` only for intentional baseline-profile work with the required device setup.
- Avoid `clean` for routine verification. Use it when diagnosing stale outputs or after a template rename.

## Module generation

Use `bash scripts/add-module.sh` with explicit flags for repeatable, non-interactive module creation. Follow [the module skill](../skills/add-android-module/SKILL.md) and inspect all generated files before keeping them.

`make template-check` proves that the rename script's dry-run is non-mutating and that both Android
and Kotlin module generation produce the expected source layout, convention plugins, namespace,
and single Gradle registration.
