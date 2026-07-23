# Architecture reference

See [`decisions.md`](decisions.md) for the rationale, consequences, and review triggers behind
project-wide constraints.

## Project shape

- `app` is the Android application, Hilt entry point, Compose UI host, and Navigation 3 integration point.
- `core/designsystem` contains reusable Compose components and shared visual tokens.
- `core/navigation` contains shared navigation state and navigator behavior.
- `library-kotlin` contains pure Kotlin/JVM logic and must not depend on Android APIs.
- `library-android` contains reusable Android-specific code and resources.
- `feature/*` contains feature-focused modules as the application grows. A stateful feature may use
  nested `domain`, `data`, and `presentation` modules when the boundaries carry real behavior.
- `feature/posts/domain` is the framework-independent posts contract and use-case module.
- `feature/posts/data` implements the posts repository, remote/local sources, DTO mapping, caching,
  and data-layer Hilt bindings.
- `feature/posts/presentation` owns the posts ViewModel, sealed UI state, route, and Compose screen.
- `benchmarks` contains macrobenchmarks and the baseline-profile generator targeting `app`.
- `build-logic` is an included build containing convention plugins; `buildSrc` contains shared build implementation.

`settings.gradle.kts` is the authoritative module list. Inspect it before assuming a module exists because template users can add, remove, or rename modules.

## Package and directory conventions

Directories must mirror Kotlin packages. Keep layer roots organized by responsibility:

- Domain: `model`, `repository`, `result`, and `usecase`.
- Data: `di`, `local`, `mapper`, `model`, `remote/api`, `remote/dto`, and `repository`.
- Presentation: `di` and `ui`; within `ui`, use `model` for display models and `components` for
  feature-local reusable composables.
- Single-module features such as `feature/home` place `HomeRoute`, `HomeScreen`, and
  `HomeViewModel` in `ui`, display models in `ui/model`, and extracted composables in
  `ui/components`.

Do not create empty directory ceremony. Add one of these subpackages when the corresponding
responsibility exists. Cross-feature reusable visual primitives belong in `core/designsystem`;
feature-specific components remain with their owning feature.

## Build boundaries

- Add dependencies and plugins to `gradle/libs.versions.toml` first, then consume catalog aliases.
- Compose module build files should apply the existing Compose convention plugin.
- Apply the existing Hilt, Room, lint, JaCoCo, and JVM/Android convention plugins instead of reproducing their configuration.
- Inspect both the convention plugin implementation and a working neighboring module before selecting a plugin. Some convention plugins may encode module dependencies or assumptions that are not appropriate everywhere.
- Avoid broad `api` dependencies. Expose a dependency only when its types intentionally form part of the module's public API.
- Keep feature internals behind module boundaries; place genuinely shared, platform-neutral behavior in an appropriate core or Kotlin module.
- For a layered feature, both `data` and `presentation` may depend on `domain`; they must not depend
  on each other. The `app` composition root depends on both and completes dependency injection.

The current intentional `api` dependencies are:

- `core/navigation` exposes Navigation 3 runtime types such as `NavKey` and `NavBackStack`.
- `core/designsystem` exposes Foundation Layout scopes such as `BoxScope` and `RowScope`.

All other external dependencies should default to `implementation`. Re-run this audit whenever a
public signature or module boundary changes.

### Explicit Kotlin visibility

Modules with meaningful feature or layer boundaries apply
`androidlab.kotlin.explicit-visibility`. The initial enforcement scope is:

- `feature/database`;
- `feature/home`;
- `feature/posts/domain`;
- `feature/posts/data`;
- `feature/posts/presentation`.

The convention enables the custom Detekt `architecture:ExplicitVisibility` rule for the standard
Detekt task. It requires an explicit `public`, `internal`, `private`, or `protected` modifier on
non-local classes and objects, named functions, properties, and primary-constructor properties.
Tests are checked too. A finding fails `./gradlew detekt` and therefore `make verify` and pull-request
CI.

Keep this opt-in selective. Add it when a module has an intentional API or layer boundary and review
that module's existing declarations before enabling it. Do not use it as a mechanical repository-wide
rewrite for host, shared-library, benchmark, or build-logic modules; those surfaces need their own
API review first.

## Android and Compose conventions

- Follow [`implementation.md`](implementation.md) for the project-wide screen, state, Flow,
  coroutine, component API, resource, accessibility, adaptive-layout, and edge-to-edge contracts.
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

Use [`testing.md`](testing.md) for test-layer selection and [`performance.md`](performance.md) for
measurement methodology.

## Files to treat as generated or sensitive

Do not edit build outputs, reports, IDE state, generated sources, dependency-guard snapshots, screenshot goldens, lint baselines, or benchmark profiles unless the requested task owns that artifact. Do not expose values from `local.properties`, keystores, environment files, or signing configuration.

Use [`security.md`](security.md) when a change affects components, intents, permissions, user data,
networking, secrets, signing, dependencies, or CI trust.
