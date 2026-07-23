# Architectural decisions

## Purpose

Record durable decisions that constrain future work. A useful decision explains why the project
chose a boundary, what alternatives were considered, the consequences, and what would justify
revisiting it.

Create or update a decision when changing:

- module ownership or dependency direction;
- navigation, persistence, dependency injection, or public API strategy;
- security or privacy boundaries;
- build conventions, version ownership, CI contracts, or release behavior;
- a pattern that future features are expected to copy.

Do not create a decision record for a local implementation detail, routine dependency update, or
reversible refactor that introduces no new project-wide constraint.

## Accepted decisions

### AD-001: Vendor-neutral agent guidance

**Status:** Accepted

**Context:** Multiple coding tools may contribute to the repository. Duplicated vendor-specific
instructions drift and create conflicting behavior.

**Decision:** [`AGENTS.md`](../../AGENTS.md) is the canonical entrypoint. Vendor adapters such as
[`CLAUDE.md`](../../CLAUDE.md) remain thin, and detailed context lives under `.agents`.

**Alternatives:** Independent vendor guides were rejected because the same rule would need to be
updated in several places. Putting agent workflow in the human-facing README was rejected because
it mixes audiences and encourages an oversized always-loaded document.

**Consequences:** Rules apply consistently across tools and context is loaded progressively. A
vendor-only capability may have an adapter, but it must not redefine repository policy.

**Review when:** A required tool cannot consume the canonical entrypoint or the shared format no
longer represents necessary path-specific guidance.

### AD-002: Version catalog and convention plugins

**Status:** Accepted

**Context:** Repeating dependency versions and Android/Kotlin configuration across modules makes
upgrades inconsistent and templates easy to misconfigure.

**Decision:** Library and Android build-plugin versions live in
[`gradle/libs.versions.toml`](../../gradle/libs.versions.toml). Shared build behavior lives in
[`build-logic/convention`](../../build-logic/convention), and modules apply the relevant convention
plugins.

**Alternatives:** Per-module versions and copied Android/Kotlin configuration were rejected because
they make template upgrades inconsistent. One oversized convention plugin was rejected because it
would hide unrelated behavior and force dependencies onto modules that do not need them.

**Consequences:** Module build files stay small and upgrades have a clear source of truth. Convention
plugin changes have a broad blast radius and require proportionate verification.

**Review when:** Gradle provides a simpler shared-configuration mechanism or a convention plugin
starts encoding feature-specific behavior.

### AD-003: Platform boundaries follow module responsibilities

**Status:** Accepted

**Context:** Android framework dependencies make business logic slower to test and harder to reuse,
while unrestricted feature dependencies erode modularity.

**Decision:** Platform-independent logic belongs in Kotlin/JVM modules. Android APIs and Compose
belong in Android modules. Feature internals stay behind feature boundaries, while genuinely shared
infrastructure belongs in an appropriate `core` module.

**Alternatives:** Keeping all code in `app` was rejected because it couples reusable logic to the
Android host. Moving convenient code into a catch-all shared module was rejected because it erases
feature ownership and creates uncontrolled dependency growth.

**Consequences:** Pure logic remains fast to test, and dependency direction is visible. Moving code
into `core` requires evidence that it is shared rather than merely convenient.

**Review when:** The project adopts multiplatform targets or a feature requires a documented public
contract across several applications.

### AD-004: Navigation 3 is the application navigation model

**Status:** Accepted

**Context:** Multiple navigation abstractions create competing back stacks, lifecycle behavior, and
deep-link ownership.

**Decision:** Use the Navigation 3 patterns in `app` and `core/navigation`. The application host owns
root navigation composition; features expose destinations and user-intent callbacks without adding
another global navigator.

**Alternatives:** A second application-wide navigation abstraction and feature-owned competing back
stacks were rejected because they duplicate lifecycle, state restoration, and deep-link ownership.

**Consequences:** Back-stack behavior has one source of truth. Navigation library migrations or
scene-model changes require coordinated app and navigation-module work.

**Review when:** Navigation 3 cannot support a required platform or scene, or measured complexity
shows that the current shared navigation layer no longer earns its cost.

### AD-005: Stateful screens separate wiring from rendering

**Status:** Accepted

**Context:** A composable that obtains dependencies, collects application state, performs
navigation, and renders a full layout is difficult to preview, test, and reuse. Applying the same
ceremony to a static screen creates abstractions without value.

**Decision:** A stateful screen has a small route/state-holder composable and a plain UI composable
that accepts immutable display state and callbacks. Static screens remain plain until state or
business behavior justifies a state holder.

**Alternatives:** Passing ViewModels through the UI tree was rejected because it hides dependencies
and couples rendering to lifecycle and DI. Requiring a ViewModel and `Flow` for every screen was
rejected because architectural ceremony is not separation of concerns.

**Consequences:** Stateful UI can be previewed and tested without the application graph, and
navigation remains an application-host concern. Feature authors must make state ownership explicit
when a screen becomes stateful.

**Review when:** A supported UI platform cannot use the split effectively, or repeated state-holder
wrappers provide no testability or ownership benefit.

### AD-006: Local and pull-request verification share one host-side contract

**Status:** Accepted

**Context:** Separately maintained local and CI command lists drift, narrow checks miss affected
modules, and automatically recording dependency or screenshot baselines can hide meaningful
changes.

**Decision:** `make verify` is the canonical host-side verification contract and the pull-request
workflow invokes it directly. It runs project-wide lint and Detekt plus deterministic screenshot,
dependency, build, test, formatting, documentation, template-tool, and build-logic checks.
Verification tasks never update baselines. Device tests remain a separate CI job because they
require managed Android infrastructure.

**Alternatives:** Duplicating individual commands in CI was rejected because local and pull-request
behavior can diverge. Automatically committing generated baselines was rejected because dependency
and visual changes require explicit human review.

**Consequences:** A local `make verify` pass exercises the same host checks as a pull request.
Baseline update targets remain available as explicit maintenance commands. CI verification jobs use
read-only repository permissions, with `security-events: write` scoped only to the job that uploads
SARIF.

**Review when:** A required host check cannot run reliably on developer machines, the managed-device
boundary changes, or GitHub's SARIF upload permission model changes.

## New decision template

```markdown
### AD-NNN: Short decision title

**Status:** Proposed | Accepted | Superseded

**Context:** What constraint or problem requires a durable decision?

**Decision:** What will the project do?

**Alternatives:** What credible options were rejected, and why?

**Consequences:** What becomes easier, harder, required, or forbidden?

**Review when:** Which evidence or project change should reopen the decision?
```

When superseding a decision, preserve the old record, change its status, and link both directions.
