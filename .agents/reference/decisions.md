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

### AD-007: Stateful data features use inward dependencies

**Status:** Accepted

**Context:** A network-backed feature needs independently testable business rules, transport
mapping, cache/error policy, lifecycle-aware state production, and Compose rendering. Keeping those
concerns in one Android module makes framework independence a convention rather than an enforced
boundary.

**Decision:** When a feature has enough real behavior to justify the split, use sibling `domain`,
`data`, and `presentation` modules under the feature. Domain is Kotlin/JVM and owns models, use
cases, failures, and repository interfaces. Data and presentation both depend inward on domain and
never on each other. The app is the composition root and depends on both implementation sides so
Hilt can complete the graph. Small or static features remain single modules until these boundaries
provide value. Within each module, source directories mirror responsibility-based packages:
`model`, `repository`, `result`, and `usecase` in domain; `di`, source, transport, mapper, and
repository packages in data; and `di`, `ui`, `ui/model`, and `ui/components` in presentation.
Single-module features use the same `ui` convention without inventing empty layer modules.

**Alternatives:** A package-only split inside one Android module was rejected for data-backed
reference features because Android and infrastructure dependencies remain available to every
package. A global `domain` or `data` catch-all was rejected because it erases feature ownership.
Requiring three modules for every screen was rejected because static UI does not earn that
complexity.

**Consequences:** Domain behavior is framework-independent and fast to test, DTOs cannot leak into
presentation through Gradle dependencies, and the app has an explicit composition role. Layered
features add module and DI wiring that must be maintained and verified.

**Review when:** Most features remain too small to benefit, the project adopts multiplatform source
sets that need different boundaries, or build measurements show the module shape creates material
cost without isolation value.

### AD-008: Feature boundaries require explicit Kotlin visibility

**Status:** Accepted

**Context:** Kotlin declarations are public by default. In feature and layered modules, an omitted
modifier can accidentally expand the module API and obscure which declarations are contracts versus
implementation details.

**Decision:** Modules with intentional feature or layer boundaries opt in to
`androidlab.kotlin.explicit-visibility`. Its custom Detekt rule checks non-local classes, objects,
named functions, properties, and primary-constructor properties in every source set. The initial
scope is `feature/database`, `feature/home`, and all three `feature/posts` layer modules. Visibility
is assigned from actual usage: file/class details are `private`, module implementation is
`internal`, and only genuine module contracts or app-facing entry points are `public`.

**Alternatives:** A repository-wide compiler flag was rejected because host, shared-library,
benchmark, and build-logic APIs have different compatibility needs and require a separate surface
review. Relying on review alone was rejected because Kotlin's implicit public default is easy to
miss and cannot protect future changes.

**Consequences:** Standard Detekt, `make verify`, and pull-request CI fail when opted-in modules omit
visibility. Enabling the plugin in another module requires a deliberate API review and an initial
visibility cleanup. The custom rule and convention plugin are part of the build-logic contract and
need focused tests.

**Review when:** Kotlin or Detekt provides an equivalent selective compiler-backed check, the
enforcement scope expands beyond feature boundaries, or maintaining the custom PSI rule becomes
more costly than its API-safety benefit.

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
