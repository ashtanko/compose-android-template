# AI workspace

This directory contains shared, vendor-neutral context for coding agents. [`../AGENTS.md`](../AGENTS.md) is the canonical contract; vendor files such as `CLAUDE.md` should only adapt or point to it.

## Layout

```text
.ai/
├── reference/                 # Project facts loaded only when relevant
│   ├── architecture.md
│   └── commands.md
├── skills/                    # Reusable task workflows
│   ├── add-android-module/
│   └── verify-android-change/
└── hooks/
    └── pre-commit             # Optional staged-file checks
```

Load `reference/architecture.md` before changing module boundaries, dependencies, navigation, or build logic. Load `reference/commands.md` when choosing validation. Use a matching skill when its frontmatter description fits the task.

The skills use the portable `SKILL.md` format. Agents without automatic skill discovery can follow the linked file directly; product-specific metadata lives beside each skill under `agents/`.

## Optional pre-commit hook

The hook syntax-checks staged shell scripts and runs `spotlessCheck` when staged Kotlin or Gradle Kotlin DSL files are present. Enable it for this clone with:

```bash
git config core.hooksPath .ai/hooks
```

This replaces any existing `core.hooksPath`. If one is already configured, invoke `.ai/hooks/pre-commit` from the existing hook instead.

## Maintenance

- Keep `AGENTS.md` short and stable; put detailed or task-specific material here.
- Keep fast-changing dependency versions in `gradle/libs.versions.toml` and link to it instead of copying values into agent docs.
- Update a skill when the corresponding workflow changes, especially `scripts/add-module.sh` or the validation tasks.
- Keep vendor adapters thin so the same rules apply to Claude, Codex, Copilot, and other agents.
