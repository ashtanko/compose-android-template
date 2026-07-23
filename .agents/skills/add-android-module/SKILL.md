---
name: add-android-module
description: Create and register an Android or pure Kotlin Gradle module using this repository's module generator and convention plugins. Use when adding a feature, core, Android library, or Kotlin/JVM library module; when deciding a new module's Gradle path and package; or when replacing ad hoc module scaffolding with the repository convention.
---

# Add Android Module

Create a module with explicit, repeatable inputs, then replace or remove generator placeholders and validate the new Gradle path.

## Workflow

1. Read [`../../reference/architecture.md`](../../reference/architecture.md) and inspect `settings.gradle.kts`, `gradle/libs.versions.toml`, `build-logic/convention`, and the nearest working module of the same type.
2. Choose:
   - `type`: `android` for Android APIs, resources, or Compose; `kotlin` for platform-independent logic.
   - `name`: lowercase letters, digits, and hyphens.
   - `parent`: usually `feature`, `core`, or an empty string for a root module.
   - `package`: a valid dotted identifier under the project's current base package.
3. Inspect the working tree and confirm the target directory and Gradle path do not already exist. Preserve unrelated edits in `settings.gradle.kts`.
4. Run the generator non-interactively:

   ```bash
   bash scripts/add-module.sh \
     --type android \
     --name profile \
     --parent feature \
     --package app.template.feature.profile
   ```

5. Review every generated file. Replace the placeholder greeting class and test with the requested implementation, or remove them if the task only calls for an empty module.
6. Generated Android modules intentionally start without explicit library dependencies. Add only
   the direct dependencies required by the implementation, default to `implementation`, and use
   `api` only when a dependency type intentionally appears in the module's public contract. Use
   catalog aliases and existing convention plugins; do not hardcode versions.
7. Confirm that the module appears exactly once in `settings.gradle.kts` and that its namespace and package path agree.
8. Run `./gradlew spotlessApply`, inspect the formatting diff, then run the module's unit-test task and `./gradlew spotlessCheck`.

## Guardrails

- Do not run the generator interactively from an unattended agent session.
- Do not overwrite an existing module or discard concurrent changes to `settings.gradle.kts`.
- Do not assume every feature needs Compose, Hilt, Room, or navigation. Add only what its implementation requires.
- Do not add convenience `api` dependencies to make libraries available transitively to consumers.
- Do not retain sample code merely to make an empty module compile; use a minimal real contract or no source file.
- Report all created files and the exact validation tasks run.
