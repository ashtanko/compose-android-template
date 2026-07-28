# Benchmark agent guide

The root [`AGENTS.md`](../AGENTS.md) applies. This file adds rules for macrobenchmarks and baseline
profiles.

- Keep benchmark code deterministic and target release-like, non-debuggable application builds.
- Use the declared managed device for deterministic baseline-profile generation. Use a stable
  physical device for representative timing measurements; emulator results are suitable only for
  smoke checks and trends tied to the same host.
- Keep setup outside measured blocks when it is not part of the user journey.
- Record the scenario, build, device, iterations, baseline, and comparison method with results.
- Cover stable, important user journeys; do not add traversal solely to increase profile size.
- Never update baseline profiles simply because generation or verification failed.
- Review package names, target project paths, and build-type assumptions after template renames.
- Keep functional assertions in the owning module; benchmarks measure behavior after correctness is
  established.

Use:

```bash
make benchmark
```

Generate profiles only when the requested change intentionally owns them:

```bash
make baseline-profile
```

Follow [`performance.md`](../.agents/reference/performance.md) for measurement and reporting
requirements.
