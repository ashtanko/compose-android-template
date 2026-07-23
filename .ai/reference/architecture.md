# Architecture reference

## Project shape

- `app` is the Android application, Hilt entry point, Compose UI host, and Navigation 3 integration point.
- `core/designsystem` contains reusable Compose components and shared visual tokens.
- `core/navigation` contains shared navigation state and navigator behavior.
- `library-kotlin` contains pure Kotlin/JVM logic and must not depend on Android APIs.
- `library-android` contains reusable Android-specific code and resources.
- `feature/*` contains feature-focused Android modules as the application grows.
- `benchmarks` contains macrobenchmarks and the baseline-profile generator targeting `app`.
- `build-logic` is an included build containing convention plugins; `buildSrc` contains shared build implementation.

`settings.gradle.kts` is the authoritative module list. Inspect it before assuming a module exists because template users can add, remove, or rename modules.

## Build boundaries

- Add dependencies and plugins to `gradle/libs.versions.toml` first, then consume catalog aliases.
- Compose module build files should apply the existing Compose convention plugin.
- Apply the existing Hilt, Room, lint, JaCoCo, and JVM/Android convention plugins instead of reproducing their configuration.
- Inspect both the convention plugin implementation and a working neighboring module before selecting a plugin. Some convention plugins may encode module dependencies or assumptions that are not appropriate everywhere.
- Avoid broad `api` dependencies. Expose a dependency only when its types intentionally form part of the module's public API.
- Keep feature internals behind module boundaries; place genuinely shared, platform-neutral behavior in an appropriate core or Kotlin module.

## Android and Compose conventions

- The app is edge-to-edge. Handle system bars and IME insets at the correct layout boundary rather than adding arbitrary padding.
- Hoist screen state and events. Keep composables focused on rendering and interaction, with previews for representative states when practical.
- Prefer immutable collections and stable state models at Compose boundaries.
- Collect flows with lifecycle awareness in UI code and keep blocking work off the main thread.
- Use Navigation 3 patterns already present in `app` and `core/navigation`; do not introduce a second navigation abstraction without an explicit architectural reason.

## Testing boundaries

- Put JVM tests in `src/test` and device/instrumentation tests in `src/androidTest`.
- Keep pure business rules testable without Android dependencies.
- Use screenshot tests for visual behavior when the affected module already owns screenshot infrastructure; update goldens only when the visual change is intentional.
- Use `benchmarks` for performance and baseline-profile work rather than placing benchmark code in application source sets.

## Files to treat as generated or sensitive

Do not edit build outputs, reports, IDE state, generated sources, dependency-guard snapshots, screenshot goldens, lint baselines, or benchmark profiles unless the requested task owns that artifact. Do not expose values from `local.properties`, keystores, environment files, or signing configuration.
