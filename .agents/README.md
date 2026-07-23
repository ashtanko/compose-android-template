# Agent workspace

This directory contains shared, vendor-neutral context for coding agents. [`../AGENTS.md`](../AGENTS.md) is the canonical contract; vendor files such as `CLAUDE.md` should only adapt or point to it.

## Layout

```text
.agents/
├── reference/                 # Project facts loaded only when relevant
│   ├── architecture.md
│   ├── commands.md
│   ├── decisions.md
│   ├── implementation.md
│   ├── performance.md
│   ├── security.md
│   └── testing.md
├── skills/                    # Reusable task workflows
│   ├── add-android-module/
│   ├── verify-android-change/
│   └── …                     # Kotlin, Compose, and issue workflows
└── hooks/
    └── pre-commit             # Optional staged-file checks
```

## Context map

| Task | Load first | Add when relevant |
| --- | --- | --- |
| Module boundaries, dependencies, navigation, or build logic | [`reference/architecture.md`](reference/architecture.md) | [`reference/decisions.md`](reference/decisions.md) |
| Implementing Android, Kotlin, or Compose behavior | [`reference/implementation.md`](reference/implementation.md) | Architecture, testing, security, performance, and focused skills as needed |
| Selecting or reviewing tests | [`reference/testing.md`](reference/testing.md) | [`reference/commands.md`](reference/commands.md) and a focused testing skill |
| Components, intents, permissions, secrets, data, or CI trust | [`reference/security.md`](reference/security.md) | The affected manifests and build files |
| Startup, runtime, Compose, size, database, or network performance | [`reference/performance.md`](reference/performance.md) | A focused performance skill and [`benchmarks/AGENTS.md`](../benchmarks/AGENTS.md) |
| Creating a module | [`skills/add-android-module/SKILL.md`](skills/add-android-module/SKILL.md) | Architecture and testing references |
| Choosing validation | [`reference/commands.md`](reference/commands.md) | [`skills/verify-android-change/SKILL.md`](skills/verify-android-change/SKILL.md) |
| Focused Kotlin or Compose work | The matching file under [`skills`](skills) | Architecture, testing, security, or performance only as needed |

The skills use the portable `SKILL.md` format. Agents without automatic skill discovery can follow the linked file directly; product-specific metadata lives beside each skill under `agents/`.

## Optional pre-commit hook

The hook syntax-checks staged shell scripts and runs `spotlessCheck` when staged Kotlin or Gradle Kotlin DSL files are present. Enable it for this clone with:

```bash
git config core.hooksPath .agents/hooks
```

This replaces any existing `core.hooksPath`. If one is already configured, invoke `.agents/hooks/pre-commit` from the existing hook instead.

## Maintenance

- Keep `AGENTS.md` short and stable; put detailed or task-specific material here.
- Keep fast-changing dependency versions in `gradle/libs.versions.toml` and link to it instead of copying values into agent docs.
- Update a skill when the corresponding workflow changes, especially `scripts/add-module.sh` or the validation tasks.
- Keep vendor adapters thin so the same rules apply to Claude, Codex, Copilot, and other agents.
- Run `make docs-check` after changing Markdown, module declarations, documented commands, or agent entrypoints.
