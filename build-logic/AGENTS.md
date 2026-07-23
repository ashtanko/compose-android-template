# Build-logic agent guide

The root [`AGENTS.md`](../AGENTS.md) applies. This file adds rules for the included Gradle build.

- Inspect the version catalog, the target convention plugin, and a neighboring convention before
  changing shared behavior.
- Keep plugin implementation dependencies `compileOnly` unless runtime behavior explicitly requires
  otherwise.
- Configure Android, Kotlin, Compose, lint, formatting, testing, coverage, and code generation in
  the existing focused convention rather than creating an all-purpose plugin.
- Do not place application or feature policy in a convention plugin.
- Treat public plugin IDs and shared defaults as cross-module APIs.
- Avoid eager project configuration and task realization; use Gradle providers and lazy task
  configuration.
- Add functional coverage when behavior cannot be proven by compilation or static checks alone.

Start validation with:

```bash
./gradlew :build-logic:convention:check
```

Broaden to `make verify` because convention changes can affect every consuming module. Consult
[`architecture.md`](../.agents/reference/architecture.md),
[`testing.md`](../.agents/reference/testing.md), and
[`decisions.md`](../.agents/reference/decisions.md) when changing a shared contract.
