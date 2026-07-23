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
- Keep vendor adapters thin so the same rules apply to Claude, Codex, Copilot, and other agents.
- Run `make docs-check` after changing Markdown, module declarations, documented commands, or agent entrypoints.

### Ownership

- The change author owns updates to affected agent references and skills in the same pull request.
- The pull-request reviewer confirms that the maintenance-impact prompts are answered and that
  durable project-wide constraints are reflected in [`reference/decisions.md`](reference/decisions.md).
- A repository maintainer owns the quarterly audit and records its outcome in a tracked issue or
  pull request rather than adding a date here that can silently become stale.

### Triggered reviews

Review the listed guidance whenever these areas change:

| Change | Required review |
| --- | --- |
| Convention plugins or shared build configuration | Architecture, decisions, commands, and verification guidance |
| `scripts/add-module.sh` or generated module structure | Architecture, the add-module skill, template checks, and human-facing setup documentation |
| CI permissions, jobs, or verification tasks | Commands, security, decisions, and the pull-request template |
| Navigation ownership, APIs, or libraries | Architecture, decisions, implementation guidance, and relevant Compose skills |
| Test infrastructure, selection rules, screenshots, or baselines | Testing, commands, verification guidance, and relevant testing skills |

### Quarterly audit

At least once per calendar quarter, a repository maintainer:

1. Reviews changes from the previous quarter for every trigger above.
2. Confirms the context map, module list, commands, examples, and decision review conditions still
   match the repository.
3. Runs `make docs-check` and records the command result.
4. Records the audit owner, references reviewed, stale references found, fixes completed, and links
   to any deferred follow-up issues.

The audit is complete when documentation checks pass and every identified gap is either fixed or
owned by a tracked follow-up.
