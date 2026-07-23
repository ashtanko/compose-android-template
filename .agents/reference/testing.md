# Testing reference

## Principle

Test the smallest contract that proves the behavior. Prefer fast, deterministic tests and add
Android framework, Compose, navigation, dependency injection, or device integration only when that
integration is the behavior under test.

## Choose the test layer

| Behavior to prove | Preferred test |
| --- | --- |
| Pure calculation, validation, mapping, or domain rule | Kotlin/JVM unit test |
| Repository or state-holder behavior | JVM unit test with fakes |
| Coroutine scheduling, cancellation, or `Flow` emissions | `runTest` and Turbine or direct collection |
| Compose content, semantics, enabled state, or callback wiring | Plain state-driven Compose test |
| Layout, typography, clipping, color, elevation, or visual focus | Screenshot test |
| Navigation, lifecycle, manifest, DI, or platform integration | Instrumentation or managed-device test |
| Startup, frame timing, or baseline-profile coverage | Macrobenchmark in `benchmarks` |

Use the command matrix in [`commands.md`](commands.md) to select the narrowest task.

## Source-set ownership

- Put platform-independent tests in `src/test`; keep their production code free of Android APIs.
- Put tests requiring Android framework behavior in the owning Android module.
- Put end-to-end navigation and application wiring tests in `app`.
- Put design-system interaction and semantics tests beside the design-system component.
- Keep macrobenchmarks and baseline-profile generation in `benchmarks`.
- Do not move logic to an Android test merely because the current production class is difficult to
  construct. Fix the boundary first when practical.

## Kotlin, coroutines, and Flow

- Prefer fakes with explicit state over broad mocks of repositories or services.
- Use `runTest`, test dispatchers, and virtual time for suspending behavior; do not use
  `runBlocking` as a test bridge.
- Assert the complete state or event sequence when order matters.
- Verify cancellation and error behavior for long-running or retrying work.
- Do not use real network, database files, wall clocks, random values, or global dispatchers in
  deterministic unit tests.
- Match the production primitive: persistent state, broadcast updates, and one-consumer events have
  different `Flow` semantics.

See [`kotlin-coroutines-structured-concurrency`](../skills/kotlin-coroutines-structured-concurrency/SKILL.md)
and [`kotlin-flow-state-event-modeling`](../skills/kotlin-flow-state-event-modeling/SKILL.md) before
adding coroutine or Flow test infrastructure.

## Compose

- Test the plain UI composable with immutable state and callbacks. Avoid constructing the whole
  application graph to test a rendering branch.
- Prefer user-visible semantics such as text, role, state, and content description. Add test tags
  only when stable semantics cannot identify the node.
- Assert callback results or state changes after interaction, not merely that a node still exists.
- Inject deterministic image loaders, clocks, animation progress, and interaction sources.
- Use screenshot tests only for visual contracts that semantics cannot prove.
- Cover representative loading, content, empty, and error states when the screen supports them.
- Test keyboard, D-pad, and focus behavior with key input and focus assertions when those input
  modes are supported.

Follow [`compose-ui-testing-patterns`](../skills/compose-ui-testing-patterns/SKILL.md) for detailed
Compose test patterns.

## Repository examples

- Pure Kotlin behavior:
  [`FactorialCalculatorTest.kt`](../../library-kotlin/src/test/java/app/template/library/FactorialCalculatorTest.kt)
- Navigation state:
  [`NavigatorTest.kt`](../../core/navigation/src/test/kotlin/app/template/core/navigation/NavigatorTest.kt)
- Design-system semantics and callbacks:
  [`TemplateComponentsTest.kt`](../../core/designsystem/src/androidTest/kotlin/app/template/core/designsystem/component/TemplateComponentsTest.kt)
- State-holder behavior:
  [`HomeViewModelTest.kt`](../../feature/home/src/test/kotlin/app/template/feature/home/HomeViewModelTest.kt)
- Plain feature UI behavior:
  [`HomeScreenTest.kt`](../../feature/home/src/androidTest/kotlin/app/template/feature/home/HomeScreenTest.kt)
- Application navigation integration:
  [`MainNavigationTest.kt`](../../app/src/androidTest/kotlin/app/template/MainNavigationTest.kt)
- Startup measurement:
  [`ExampleStartupBenchmark.kt`](../../benchmarks/src/main/java/dev/shtanko/template/benchmarks/ExampleStartupBenchmark.kt)

Treat these as current examples, not permanent exceptions. Improve the example when the recommended
project pattern changes.

## Change expectations

| Change | Expected evidence |
| --- | --- |
| Business rule or bug fix | Focused unit regression test |
| State-holder or Flow behavior | State/event sequence test |
| Compose behavior | Plain UI semantics/callback test |
| Intent, permission, or exported component | Hostile-input or access-control test plus lint |
| Intentional visual change | Screenshot verification and reviewed baseline update |
| Navigation or DI wiring | Small integration smoke test |
| Performance-sensitive path | Before/after measurement using the same setup |

Do not regenerate screenshot, dependency, lint, or baseline-profile artifacts merely to make a
verification task pass.

## Definition of done

- The test fails for the old behavior and passes for the intended behavior when a regression is
  being fixed.
- The lowest useful layer owns most assertions; integration coverage is intentionally small.
- External inputs and time are deterministic.
- The narrow owning-module check passes, followed by broader checks in proportion to the change.
- The final report lists exact commands and anything not run.
