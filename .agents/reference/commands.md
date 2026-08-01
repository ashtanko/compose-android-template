# Commands and validation

Run commands from the repository root with the Gradle wrapper. JDK 21 is required.

## Focused commands

| Change | Start with |
| --- | --- |
| Documentation only | `make docs-check` |
| Template tooling | `make template-check` |
| Android string resources or translations | `make localization-check` |
| Sensitive files or credentials | `make secrets-check` |
| Release signing configuration | `./gradlew :app:validateReleaseSigningConfiguration` |
| Shell script | `bash -n path/to/script.sh` plus a safe dry run when supported |
| Pure Kotlin module | `./gradlew :module:test` |
| JVM integration | `./gradlew :module:integrationTest` |
| Android module | `./gradlew :module:testDebugUnitTest` |
| App unit behavior | `./gradlew :app:testDebugUnitTest` |
| Formatting | `./gradlew spotlessCheck` |
| Static analysis | `./gradlew detekt` |
| Compose-specific static analysis | `./gradlew detektCompose` |
| Android lint | `./gradlew lint` or `./gradlew :module:lintDebug` |
| Screenshot verification | `./gradlew validateDebugScreenshotTest` |
| One module's instrumentation | `./gradlew :module:connectedDebugAndroidTest` with a device or emulator available |
| Project managed-device suite | `make device-test-ci` |
| Macrobenchmark | `./gradlew :benchmarks:connectedBenchmarkReleaseAndroidTest` on a stable physical device |
| Baseline profile generation | `./gradlew :app:generateBaselineProfile` using the declared managed device |

Replace `:module` with the actual Gradle path, for example `:core:navigation`. Use `--tests "fully.qualified.ClassName"` to narrow a unit-test task when iterating.

`make docs-check` validates local Markdown links, documented Make targets, module references,
the canonical agent entrypoint, and version-policy consistency without starting Gradle.

`make localization-check` runs the localization tool's unit tests, discovers locale-specific
resources in every Android module, and checks common production Compose literals, translation
completeness, and formatter compatibility. Use
`make localization-report LOCALE=pt-PT FORMAT=csv` to produce a review catalog.

`make secrets-check` scans every file in the Git index for forbidden credential paths, private-key
material, common high-confidence token formats, and hardcoded Android signing passwords. The
pre-commit hook runs the same scanner against staged additions and modifications. The dedicated
`secret-check.yml` GitHub Actions workflow runs for every pull request, including documentation-only
changes that the Android build workflow intentionally skips.

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

It validates documentation, template tools, localization resources, and tracked files for secrets;
checks build logic;
assembles debug artifacts; and runs unit and JVM integration tests, coverage reporting and
verification, lint, Detekt, Spotless, Dependency Guard, and Compose screenshot validation without requiring release signing. The host-side
pull-request job invokes this exact target; managed-device tests remain a separate
environment-dependent CI job.

Routine verification never records baselines. Use `make screenshot-record` or
`make dependency-guard-baseline` only when the corresponding change is
intentional, then review every generated diff.

`make device-test-ci` runs every module's debug instrumentation tests and `tests/e2e` journeys on
the managed phone and tablet group used by CI. `make device-test-all` expands to every declared
managed device. These tasks are intentionally separate from the host contract because they require
Android system images and virtualization. Run `make coverage` after the device suite when a local
combined Android unit-and-instrumentation coverage report is required; CI does this automatically.

## Release build

Run `make generate-release-key` to interactively create a new upload keystore and the ignored local
signing properties file. The generator refuses to overwrite either output.

Run `make release` to build the signed release Android App Bundle. It reads a complete untracked
`key.properties` file locally or the complete documented signing environment on CI, disables
configuration caching for the signing invocation, and fails if credentials or the keystore are
missing. Routine `make verify` and pull-request CI remain debug-only and do not require release
secrets. See [`RELEASING.md`](../../RELEASING.md) for credential setup and the protected manual
GitHub Actions workflow.

## Mutating commands

- Use `./gradlew spotlessApply` only when formatting changes are in scope; review its diff afterward.
- Use `./gradlew :app:dependencyGuardBaseline` only for an intentional dependency-surface change.
- Use `./gradlew :app:generateBaselineProfile` only for intentional baseline-profile work with the required device setup.
- Avoid `clean` for routine verification. Use it when diagnosing stale outputs or after a template rename.

## Module generation

Use `bash scripts/add-module.sh` with explicit flags for repeatable, non-interactive module creation. Follow [the module skill](../skills/add-android-module/SKILL.md) and inspect all generated files before keeping them.

`make template-check` copies the tracked repository into a temporary fixture, proves that a rename
dry-run is non-mutating, performs a real rename with XML/Kotlin-sensitive characters, checks all
package and screenshot-reference moves, verifies service-provider and helper-script updates,
rejects invalid identifiers, and creates Android and Kotlin modules from the renamed defaults.
