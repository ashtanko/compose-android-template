# Repository agent guide

This file is the canonical entry point for coding agents working in this repository. It applies to the entire tree unless a nested `AGENTS.md` says otherwise.

## Start here

- Read [`.agents/README.md`](.agents/README.md) for the task-specific context map.
- Load only the relevant reference or skill; do not pull every AI document into context.
- Treat [`README.md`](README.md) as the human-facing product overview, not as the source of agent workflow rules.

## Repository rules

- Use the Gradle wrapper and JDK 21. Do not rely on a globally installed Gradle.
- Preserve unrelated work in a dirty worktree. Inspect the diff before editing and never clean up changes you did not make.
- Keep dependency and plugin versions in `gradle/libs.versions.toml`; do not hardcode versions in module build files.
- Reuse the convention plugins in `build-logic/convention` instead of duplicating Android, Kotlin, Compose, Hilt, Room, lint, coverage, or formatting setup.
- Put platform-independent logic in a Kotlin/JVM module. Keep Android APIs and Compose code in Android modules.
- Do not edit generated output under `build/`, `.gradle/`, `.kotlin/`, IDE state, reports, dependency snapshots, screenshot goldens, or baselines unless the task explicitly requires it.
- Never commit `local.properties`, production signing credentials, production keystores, environment files, or real secrets. The repository's template debug keystore may remain. Preserve the existing CI environment-variable contract for signing.
- Follow `.editorconfig`, Detekt, KtLint, and Spotless. Prefer immutable UI state and lifecycle-aware `Flow` collection in Compose code.

## Working method

1. Inspect the target module, neighboring implementations, its `build.gradle.kts`, and the current diff.
2. Make the smallest coherent change that follows existing package and module boundaries.
3. Add or update tests with behavior changes. Use previews or screenshot tests for meaningful visual state changes where the module already supports them.
4. Run the narrowest useful checks first, then broaden checks in proportion to the change. See [`.agents/reference/commands.md`](.agents/reference/commands.md).
5. Report changed files, checks run, and anything not verified. Never claim a check passed if it was not run.

## Task-specific guidance

- Architecture and module placement: [`.agents/reference/architecture.md`](.agents/reference/architecture.md)
- Commands and validation matrix: [`.agents/reference/commands.md`](.agents/reference/commands.md)
- Creating a module: [`.agents/skills/add-android-module/SKILL.md`](.agents/skills/add-android-module/SKILL.md)
- Selecting checks for a change: [`.agents/skills/verify-android-change/SKILL.md`](.agents/skills/verify-android-change/SKILL.md)
