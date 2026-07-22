---
name: verify-android-change
description: Select and run proportionate checks for changes in this Android and Kotlin repository. Use after modifying Kotlin, Compose, Gradle, resources, shell scripts, tests, dependencies, screenshots, benchmarks, or AI guidance; when diagnosing a failed local check; or before reporting an implementation complete.
---

# Verify Android Change

Validate the behavior that changed first, then expand only as risk and scope justify. Read [`../../reference/commands.md`](../../reference/commands.md) for the command matrix.

## Workflow

1. Inspect `git status --short`, the relevant diff, untracked files in scope, and the affected module build files. Separate pre-existing user work from the current change.
2. Map changed files to behavior and Gradle modules. Account for downstream modules when public APIs, convention plugins, the version catalog, or shared resources changed.
3. Run the narrowest deterministic check:
   - documentation: verify local links, paths, and command examples;
   - shell: `bash -n` and a supported dry run;
   - JVM logic: the owning module's `test` task, narrowed with `--tests` while iterating;
   - Android logic or Compose state: the owning module's `testDebugUnitTest` task;
   - resources, manifest, or Android configuration: the owning module's `lintDebug` or assemble task.
4. Run `./gradlew spotlessCheck` for Kotlin or Gradle Kotlin DSL changes. Run Detekt and Android lint when production code or build configuration changed.
5. Broaden to `./gradlew build lint detekt spotlessCheck` for shared build logic, dependency changes, public API changes, or pre-PR verification.
6. Recheck the diff after any formatter, generator, baseline task, or build that may produce tracked files.
7. Report the exact commands and outcomes. Explain skipped device, screenshot, benchmark, or environment-dependent checks.

## Visual and baseline changes

- Verify screenshots when UI output changed and screenshot coverage exists.
- Never update screenshot goldens, dependency-guard baselines, lint baselines, or baseline profiles merely to make a check pass.
- Review every generated artifact when an intentional baseline update is part of the request.

## Failure handling

- Read the first actionable failure and distinguish a source defect from a missing SDK, unavailable device, network problem, or pre-existing unrelated failure.
- Fix implementation failures that are in scope, then rerun the narrow check before the broad suite.
- Do not hide failures with exclusions, relaxed rules, or regenerated baselines unless the task explicitly changes that policy.
