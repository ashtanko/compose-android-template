# Android and Kotlin implementation reference

## Principle

Use the smallest architecture that gives the behavior a clear owner. Static UI does not need a
ViewModel, repository, use case, `Flow`, or event stream. Add those boundaries when state,
asynchronous work, persistence, sharing, or business rules make them useful.

This file defines project-wide implementation contracts. Load the focused skill linked from each
section before making a non-trivial change in that area.

## Module and API ownership

- `app` owns the Android application, root dependency graph, top-level theme application, and root
  Navigation 3 composition.
- `feature/*` owns feature UI, feature state holders, and feature-specific data orchestration.
- `core/designsystem` owns reusable visual tokens and Compose components, not product workflows.
- `core/navigation` owns shared back-stack primitives and behavior, not feature UI.
- Kotlin/JVM modules own platform-independent rules and models that do not need Android APIs.
- Android library modules own reusable behavior that genuinely requires Android APIs or resources.
- Do not add feature-to-feature dependencies without an accepted architectural decision. Move a
  genuinely shared contract to an appropriate `core` or Kotlin/JVM module.
- Keep feature implementation types internal where possible. Use Gradle `api` only when a dependency
  type intentionally appears in the module's public contract.
- Reuse convention plugins. Do not recreate Android, Kotlin, Compose, Hilt, Room, lint, formatting,
  coverage, or test configuration in individual modules.

Read [`architecture.md`](architecture.md) and [`decisions.md`](decisions.md) before changing these
boundaries.

## Screen structure

For a stateful screen, separate state-holder wiring from plain UI rendering:

```kotlin
@Composable
fun ProfileRoute(
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ProfileViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    ProfileScreen(
        state = state,
        onRetryClick = viewModel::retry,
        onBackClick = onBackClick,
        modifier = modifier,
    )
}

@Composable
fun ProfileScreen(
    state: ProfileUiState,
    onRetryClick: () -> Unit,
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    // Render state and invoke callbacks only.
}
```

The compiled reference is
[`HomeRoute.kt`](../../feature/home/src/main/kotlin/app/template/feature/home/HomeRoute.kt) with
[`HomeScreen.kt`](../../feature/home/src/main/kotlin/app/template/feature/home/HomeScreen.kt).
Keep this shape aligned with that feature as the template evolves.

- The route/state-holder composable may obtain injected objects, collect lifecycle-aware state, and
  handle imperative effects.
- The plain screen composable accepts immutable display state and intent-style callbacks. It does
  not know about Hilt, repositories, navigation objects, or lifecycle collection.
- Navigation is a callback from feature UI. The application host decides how that intent changes
  the back stack.
- Do not create both functions when the screen is static or the split adds no isolation.
- Do not pass a ViewModel, component, repository, or navigator through the child composable tree.
- Keep previews and most Compose tests on the plain UI function.

Follow
[`compose-state-holder-ui-split`](../skills/compose-state-holder-ui-split/SKILL.md) and
[`compose-side-effects`](../skills/compose-side-effects/SKILL.md).

## State ownership

| State | Owner |
| --- | --- |
| One composable's simple expansion, interaction, or animation state | Local `remember` |
| Serializable UI input that should survive recreation | Local `rememberSaveable` |
| UI state shared by sibling composables | Lowest common composable owner |
| Coordinated scroll, focus, sheet, or text-field behavior | Plain composition-owned state holder |
| Repository data, persistence, business rules, or screen state production | Screen state holder |

- Hoist only as far as the logic needs the state.
- Keep Compose runtime objects such as `LazyListState`, `FocusRequester`, and animation state out of
  ViewModels.
- Save the minimum serializable values needed to reconstruct UI behavior, not framework objects.
- Prefer immutable UI-state properties and explicit loading, content, empty, and error states when
  those are real states.
- Do not invent fake domain values merely to satisfy a `StateFlow` initial value.
- Do not add `@Stable` or `@Immutable` as a speculative performance fix; the annotated contract must
  be true and compiler/profiler evidence should justify performance work.

Follow [`compose-state-hoisting`](../skills/compose-state-hoisting/SKILL.md) and
[`compose-state-authoring`](../skills/compose-state-authoring/SKILL.md).

## Flow state and events

Choose primitives by replay, fan-out, durability, and synchronous-read requirements:

| Requirement | Default primitive |
| --- | --- |
| Observable state with a current value | `StateFlow` |
| Cold data stream that starts per collector | `Flow` |
| Hot broadcast where every active subscriber should observe emissions | Deliberately configured `SharedFlow` |
| One in-process UI consumer receives a discrete handoff | Buffered `Channel` exposed as `Flow` |
| Outcome must survive collector absence or process recreation | Durable state or persistence |

- Mutate `MutableStateFlow` with `update`; keep the transform fast, pure, and free of side effects.
- Create shared state once as a property. Do not call `stateIn` from a function that creates a new
  sharing coroutine on every invocation.
- Select `SharingStarted` from actual lifecycle and synchronous-read needs. Do not use
  `WhileSubscribed` when `.value` must stay fresh without collectors.
- A default `MutableSharedFlow` can drop navigation or snackbar events while no collector is active.
- A channel-backed flow distributes each element to one collector; it is not broadcast and does not
  make an event durable.
- Prefer a direct callback for an immediate UI navigation intent. Add an effect stream when an
  asynchronous state-holder result must trigger imperative UI behavior.

Follow
[`kotlin-flow-state-event-modeling`](../skills/kotlin-flow-state-event-modeling/SKILL.md).

## Coroutines and background work

- Repositories, use cases, managers, and data sources expose suspending APIs. Their callers choose
  the lifecycle and scope.
- A UI state holder may translate a non-suspending UI callback into work launched in
  `viewModelScope`; that is the intended UI boundary.
- Do not store or create an ad-hoc `CoroutineScope` in a non-lifecycle owner.
- Do not launch hidden work from constructors, `init` blocks, or dependency-injection initializers.
  Use an explicit suspending entrypoint and a visible lifecycle owner.
- Use WorkManager for genuinely deferred or guaranteed work.
- Never swallow `CancellationException` through a broad catch or `runCatching`.
- Do not use `runBlocking` in suspend-capable application code. Keep unavoidable synchronous bridges
  at framework or interoperability boundaries and keep them small.
- Use `runTest` and virtual time for coroutine tests.

Follow
[`kotlin-coroutines-structured-concurrency`](../skills/kotlin-coroutines-structured-concurrency/SKILL.md).

## Compose component APIs

- A composable that emits layout accepts `modifier: Modifier = Modifier`, placed after required
  parameters and before optional content parameters.
- Apply the caller's modifier to the root. The caller owns placement, outer size, and screen-level
  padding; the component owns only modifiers intrinsic to its identity.
- Build modifiers as one fluent expression. Format chains of three or more calls with one call per
  line.
- Use slots for variable visual regions of a reusable component. Use nullable slots with a `null`
  default when the region is optional so absent content does not reserve space.
- Give a slot a `RowScope`, `ColumnScope`, or `BoxScope` receiver only when it is emitted in that
  layout and callers need the scope operations.
- Keep repeated component defaults in an `XxxDefaults` object.
- Do not add slot ceremony to a true single-use composable or to a primitive that intentionally
  constrains every caller to the same visual contract.
- Prefer Material and design-system tokens over feature-local hardcoded colors, shapes, typography,
  and spacing.

Follow
[`compose-modifier-and-layout-style`](../skills/compose-modifier-and-layout-style/SKILL.md) and
[`compose-slot-api-pattern`](../skills/compose-slot-api-pattern/SKILL.md).

## Resources and accessibility

- Put user-visible production text in resources. Use formatted strings and plurals instead of
  concatenating localized fragments.
- Hardcoded text is acceptable in previews, tests, logs, and developer-only diagnostics.
- Give actionable icons and images a meaningful label. Mark decorative imagery with a null content
  description so accessibility services skip it.
- Expose roles, selected/checked/expanded state, headings, errors, and state descriptions through
  semantics when the visual alone is insufficient.
- Preserve minimum interactive target sizes and do not make visual size the only interaction cue.
- Verify large font scales, long translations, RTL layout, keyboard input, and focus behavior for
  affected components.
- Prefer semantics assertions for behavior and screenshots for visual contracts.

Use [`testing.md`](testing.md) and
[`compose-focus-navigation`](../skills/compose-focus-navigation/SKILL.md) for verification.

## Adaptive layouts

- Adapt to the current window and input capabilities, not device model names or a one-time
  orientation check.
- Use Material adaptive navigation components so compact windows can use bottom navigation and
  larger windows can use rails or other suitable navigation areas.
- Model list-detail and supporting-pane layouts with Navigation 3 scene strategies so the same back
  stack can render one or multiple panes.
- Give repeated content a meaningful minimum width and adapt the column count from available space.
- Require an explicit decision before adopting an experimental layout API.
- Add representative previews or screenshot scenarios for compact, foldable, and expanded windows
  when adaptive behavior changes.
- Test keyboard, D-pad, mouse, and touch input when the target form factors support them.

## Edge-to-edge and IME

- Every Activity uses the project's edge-to-edge setup. The current entrypoint is
  [`EdgeToEdgeCompat.kt`](../../app/src/main/kotlin/app/template/ui/EdgeToEdgeCompat.kt).
- Assign each inset to one owner. Do not stack Scaffold padding, safe-area padding, and IME padding
  for the same inset.
- Pass Scaffold `innerPadding` to scrollable content through `contentPadding` so items can scroll
  behind bars while first and last items remain reachable.
- Consume padding values when passing them down to nested content that might otherwise apply the
  same insets again.
- For screens with text input, use manifest resize behavior and one deliberate IME inset strategy.
  Verify that focused fields remain visible and that opening the keyboard does not add double
  padding.
- Let Material components manage their supported insets; add manual handling only at custom layout
  boundaries.
- Keep system-bar icons legible in light and dark themes and verify gesture and three-button
  navigation.

## Review checklist

- Is every new layer justified by real state, behavior, ownership, or reuse?
- Can the plain screen render and be tested without DI, navigation, or lifecycle objects?
- Does every coroutine have a visible lifecycle owner and preserve cancellation?
- Does each Flow primitive match its replay, fan-out, and durability requirements?
- Does the component let its parent place it and callers supply genuinely variable content?
- Are text, semantics, adaptive behavior, system insets, IME, and alternate input modes handled?
- Do tests follow [`testing.md`](testing.md), and do performance or security changes load their
  focused references?
