# Performance reference

## Principle

Measure before optimizing, change one cause at a time, and re-measure with the same build, device,
data, and interaction. A faster-looking debug build is not performance evidence.

Record the metric, device or managed-device definition, build type, scenario, iteration count,
baseline result, and acceptable regression before starting significant performance work. Do not
invent a universal budget when the product has not selected one.

## Performance areas

| Area | Evidence | Repository mechanism |
| --- | --- | --- |
| Startup | Cold/warm startup timing and trace | Macrobenchmark |
| Runtime interaction | Frame timing, jank, trace slices | Macrobenchmark and Perfetto |
| Compose | Recomposition counts and compiler reports | Layout Inspector, Compose compiler, Compose Guard |
| App size and shrinking | APK analysis and release build behavior | R8 and dependency review |
| Database/network | Query, serialization, payload, and dispatcher timing | Focused benchmarks and traces |
| Installation optimization | Covered startup/user journeys | Baseline profiles |

The benchmark module and its target are described in
[`benchmarks/AGENTS.md`](../../benchmarks/AGENTS.md).

## Compose investigation order

1. Reproduce one specific transition and confirm that the extra work is measurable.
2. Verify that recomposition is not simply tracking a real state change.
3. Check for snapshot-state writes during composition or layout-to-composition back-writing.
4. Check whether scroll, gesture, or animation state can be read later in layout or draw.
5. Check parameter stability and instance churn only after the read/write path is understood.
6. Re-measure after each change and retain only changes supported by evidence.

Start with
[`compose-recomposition-performance`](../skills/compose-recomposition-performance/SKILL.md), which
routes stability issues to
[`compose-stability-diagnostics`](../skills/compose-stability-diagnostics/SKILL.md) and high-frequency
reads or back-writing to
[`compose-state-deferred-reads`](../skills/compose-state-deferred-reads/SKILL.md).

Avoid speculative annotations, memoization, immutable-collection conversions, or custom stability
configuration without compiler or profiler evidence.

## Startup and runtime

- Measure release-like, non-debuggable builds; debugging and inspection can distort results.
- Keep benchmark setup deterministic and exclude setup work from the measured block where possible.
- Use stable local data or a controlled fake backend for repeatable journeys.
- Trace slow startup before moving initialization blindly to another dispatcher.
- Delay nonessential work only when the resulting lifecycle, cancellation, and user-visible behavior
  are explicit.
- Use WorkManager for genuinely deferred or guaranteed background work rather than long-lived
  ad-hoc coroutine scopes.

The current examples are
[`ExampleStartupBenchmark.kt`](../../benchmarks/src/main/java/dev/shtanko/template/benchmarks/ExampleStartupBenchmark.kt)
and
[`BaselineProfileGenerator.kt`](../../benchmarks/src/main/java/dev/shtanko/template/benchmarks/BaselineProfileGenerator.kt).

## Baseline profiles

- Cover stable, important user journeys rather than every screen.
- Keep profile generation deterministic and review generated changes.
- Regenerate only when the task intentionally changes covered journeys or profile configuration.
- Benchmark before and after changing the profile; generation success alone does not prove a gain.
- Never edit generated profile output manually.

## App size, R8, and dependencies

- Test optimized release-like builds when changing reflection, serialization, JNI, or keep rules.
- Prefer precise consumer rules owned by the library that requires them.
- Review Dependency Guard changes for accidental transitive growth.
- Compare APK contents before adding broad keep rules or large UI/icon artifacts.
- Treat startup improvements that significantly increase binary size as a tradeoff requiring an
  explicit decision.

## Database and network

- Keep disk, database, and network work off the main thread.
- Measure actual query plans, payloads, pagination, and serialization before adding caches.
- Bound caches and document invalidation; an unbounded cache is a memory leak with good marketing.
- Avoid per-item I/O and repeated object creation in scrolling paths.
- Include error, empty, cached, and slow-response scenarios when they materially affect perceived
  performance.

## Validation

- Run the narrow functional tests first; performance changes must preserve behavior.
- Use `make benchmark` for macrobenchmarks and `make baseline-profile` only for intentional profile
  generation.
- Use the screenshot and Compose tests appropriate to UI changes.
- Attach before/after results and methodology to the pull request.
- Explain when a device, trace, or release-signing requirement prevented local verification.
