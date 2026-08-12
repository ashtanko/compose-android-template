#!/usr/bin/env python3
"""Flexible CLI and browser-based setup wizard for this Android template."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import replace
from pathlib import Path

from setup_wizard.engine import (
    SetupError,
    apply_plan,
    build_plan,
    create_archive,
    default_source_root,
    read_project_settings,
)
from setup_wizard.model import (
    CAPABILITIES,
    PRESETS,
    IdentityConfig,
    OutputConfig,
    ProjectSettingsConfig,
    SetupConfig,
    StarterConfig,
    ValidationConfig,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Configure project identity, starter modules, and curated dependencies. "
            "Plans are previews unless --apply is supplied."
        ),
    )
    parser.add_argument("--ui", action="store_true", help="open the local browser wizard")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="serve the download-only wizard on 0.0.0.0:$PORT",
    )
    parser.add_argument("--config", type=Path, help="load a versioned JSON configuration")
    parser.add_argument("--export-config", type=Path, help="write the resolved JSON configuration")
    parser.add_argument("--package", dest="package_name")
    parser.add_argument("--name", dest="project_name")
    parser.add_argument("--application-id")
    parser.add_argument("--display-name")
    parser.add_argument("--plugin-alias")
    parser.add_argument("--author")
    parser.add_argument("--version-code", type=int)
    parser.add_argument("--version-name")
    parser.add_argument("--compile-sdk", type=int)
    parser.add_argument("--min-sdk", type=int)
    parser.add_argument("--target-sdk", type=int)
    parser.add_argument("--benchmark-min-sdk", type=int)
    parser.add_argument(
        "--posts-backend-url",
        help="HTTPS Retrofit base URL used when example modules are retained",
    )
    parser.add_argument(
        "--preset",
        choices=(*PRESETS.keys(), "custom"),
        help="start from a curated dependency preset",
    )
    parser.add_argument(
        "--capability",
        action="append",
        choices=[capability.id for capability in CAPABILITIES],
        help="enable an additional capability; may be repeated",
    )
    examples = parser.add_mutually_exclusive_group()
    examples.add_argument(
        "--remove-examples",
        dest="remove_examples",
        action="store_true",
    )
    examples.add_argument(
        "--keep-examples",
        dest="remove_examples",
        action="store_false",
    )
    ai_mode = parser.add_mutually_exclusive_group()
    ai_mode.add_argument(
        "--ai-free",
        dest="ai_free",
        action="store_true",
        help="remove coding-agent guidance and generative-AI integration",
    )
    ai_mode.add_argument(
        "--include-ai",
        dest="ai_free",
        action="store_false",
        help="retain coding-agent guidance and optional generative-AI integration",
    )
    parser.set_defaults(remove_examples=None, ai_free=None)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--output", type=Path, help="create a configured project copy")
    output.add_argument("--in-place", action="store_true", help="configure this clone")
    output.add_argument("--archive", type=Path, help="write a configured ZIP archive")
    parser.add_argument("--format", action="store_true", dest="apply_formatting")
    parser.add_argument("--verify", choices=("none", "narrow", "full"))
    parser.add_argument("--apply", action="store_true", help="apply the reviewed plan")
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow in-place setup in a dirty worktree",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.ui or args.serve:
        if args.ui and args.serve:
            raise SetupError("--ui and --serve cannot be combined")
        if _has_cli_configuration(args):
            mode = "--serve" if args.serve else "--ui"
            raise SetupError(
                f"{mode} cannot be combined with CLI configuration options",
            )
        from setup_wizard.server import run_server

        run_server(default_source_root(), public=args.serve)
        return 0

    interactive = (
        args.config is None
        and args.package_name is None
        and args.project_name is None
        and sys.stdin.isatty()
    )
    if interactive:
        config = guided_config()
    else:
        config = config_from_args(args)

    plan = build_plan(config)
    print_plan(plan)

    if args.export_config:
        args.export_config.write_text(plan.config.to_json(), encoding="utf-8")
        print(f"\nExported configuration to {args.export_config}")

    should_apply = args.apply
    if interactive and not should_apply:
        answer = input("\nApply this plan? [y/N]: ").strip().lower()
        should_apply = answer in {"y", "yes"}
    if not should_apply:
        print("\nPreview only. Re-run with --apply to generate the project.")
        return 0

    if plan.config.output.mode == "archive":
        body, filename = create_archive(plan, expected_digest=plan.digest)
        archive_path = args.archive or (Path.cwd() / filename)
        if archive_path.exists():
            raise SetupError(f"archive already exists: {archive_path}")
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.write_bytes(body)
        print(f"\nProject archive created: {archive_path}")
    else:
        result = apply_plan(plan, expected_digest=plan.digest, force=args.force)
        print(f"\nProject setup completed: {result}")
    return 0


def config_from_args(args: argparse.Namespace) -> SetupConfig:
    if args.config:
        try:
            config = SetupConfig.from_json_file(args.config)
        except ValueError as error:
            raise SetupError(str(error)) from error
    else:
        if not args.package_name or not args.project_name:
            raise SetupError(
                "--package and --name are required without --config "
                "(or run interactively in a terminal)",
            )
        preset = args.preset or "standard"
        requested = set() if preset == "custom" else set(PRESETS[preset])
        requested.update(args.capability or ())
        remove_examples = (
            True if args.remove_examples is None else args.remove_examples
        )
        output = _output_from_args(args, args.project_name)
        config = SetupConfig(
            identity=IdentityConfig(
                package_name=args.package_name,
                project_name=args.project_name,
                application_id=args.application_id,
                display_name=args.display_name,
                plugin_alias=args.plugin_alias,
                author=args.author,
            ),
            output=output,
            starter=StarterConfig(
                remove_examples=remove_examples,
                ai_free=bool(args.ai_free),
            ),
            project_settings=ProjectSettingsConfig(
                version_code=args.version_code,
                version_name=args.version_name,
                compile_sdk=args.compile_sdk,
                min_sdk=args.min_sdk,
                target_sdk=args.target_sdk,
                benchmark_min_sdk=args.benchmark_min_sdk,
                posts_backend_url=args.posts_backend_url,
            ),
            capabilities=frozenset(requested),
            validation=ValidationConfig(
                format=args.apply_formatting,
                level=args.verify or "none",
            ),
        )

    identity = config.identity
    if args.package_name:
        identity = replace(identity, package_name=args.package_name)
    if args.project_name:
        identity = replace(identity, project_name=args.project_name)
    if args.application_id:
        identity = replace(identity, application_id=args.application_id)
    if args.display_name:
        identity = replace(identity, display_name=args.display_name)
    if args.plugin_alias:
        identity = replace(identity, plugin_alias=args.plugin_alias)
    if args.author:
        identity = replace(identity, author=args.author)

    starter = config.starter
    if args.remove_examples is not None:
        starter = replace(starter, remove_examples=args.remove_examples)
    if args.ai_free is not None:
        starter = replace(starter, ai_free=args.ai_free)

    project_settings = config.project_settings
    for attribute, value in (
        ("version_code", args.version_code),
        ("version_name", args.version_name),
        ("compile_sdk", args.compile_sdk),
        ("min_sdk", args.min_sdk),
        ("target_sdk", args.target_sdk),
        ("benchmark_min_sdk", args.benchmark_min_sdk),
        ("posts_backend_url", args.posts_backend_url),
    ):
        if value is not None:
            project_settings = replace(
                project_settings,
                **{attribute: value},
            )

    capabilities = set(config.capabilities)
    if args.preset:
        capabilities = (
            set()
            if args.preset == "custom"
            else set(PRESETS[args.preset])
        )
    capabilities.update(args.capability or ())

    validation = config.validation
    if args.apply_formatting:
        validation = replace(validation, format=True)
    if args.verify:
        validation = replace(validation, level=args.verify)

    output = config.output
    if args.output or args.in_place or args.archive:
        output = _output_from_args(args, identity.project_name)

    return replace(
        config,
        identity=identity,
        output=output,
        starter=starter,
        project_settings=project_settings,
        capabilities=frozenset(capabilities),
        validation=validation,
    )


def _output_from_args(args: argparse.Namespace, project_name: str) -> OutputConfig:
    if args.in_place:
        return OutputConfig(mode="inPlace")
    if args.archive:
        return OutputConfig(mode="archive")
    output = args.output
    if output is None:
        slug = re.sub(r"[^a-z0-9]+", "-", project_name.lower()).strip("-")
        output = Path.cwd().parent / (slug or "android-project")
    return OutputConfig(mode="copy", path=str(output))


def guided_config() -> SetupConfig:
    print("\nProject Setup Wizard")
    print("Configure identity, examples, dependencies, and validation.\n")
    project_name = _prompt_required("Project name")
    package_name = _prompt_required("Package name (for example com.example.app)")
    display_name = _prompt_default("App display name", project_name)
    application_id = _prompt_default("Application ID", package_name)
    author = input("Author (optional): ").strip() or None
    plugin_alias = input("Plugin alias (derived when empty): ").strip() or None

    defaults = read_project_settings(default_source_root())
    print("\nApp version and Android SDK settings:")
    version_code = _prompt_integer("Version code", defaults.version_code)
    version_name = _prompt_default("Version name", defaults.version_name)
    compile_sdk = _prompt_integer("Compile SDK", defaults.compile_sdk)
    min_sdk = _prompt_integer("Minimum SDK", defaults.min_sdk)
    target_sdk = _prompt_integer("Target SDK", defaults.target_sdk)
    benchmark_min_sdk = _prompt_integer(
        "Benchmark minimum SDK",
        defaults.benchmark_min_sdk,
    )
    print(f"JVM target: {defaults.jvm_target} (fixed by the JDK/CI contract)")

    print("\nDependency preset:")
    print("  1) Standard — recommended app stack")
    print("  2) Minimal — Compose foundations only")
    print("  3) Full — every supported capability")
    print("  4) Custom — select capability groups")
    preset_choice = input("Choice [1]: ").strip() or "1"
    preset_by_choice = {"1": "standard", "2": "minimal", "3": "full", "4": "custom"}
    if preset_choice not in preset_by_choice:
        raise SetupError("invalid dependency preset choice")
    preset = preset_by_choice[preset_choice]
    capabilities = (
        set()
        if preset == "custom"
        else set(PRESETS[preset])
    )
    if preset == "custom":
        capabilities = _prompt_capabilities()

    remove_examples = _prompt_yes_no(
        "Remove example modules and create a minimal starter?",
        default=True,
    )
    ai_free = _prompt_yes_no(
        "Create an AI-free project (remove agent guidance and AI integration)?",
        default=False,
    )
    posts_backend_url = None
    if not remove_examples:
        posts_backend_url = _prompt_default(
            "Posts example backend URL",
            defaults.posts_backend_url,
        )
    create_archive_output = _prompt_yes_no(
        "Create a downloadable ZIP archive?",
        default=True,
    )
    if create_archive_output:
        output = OutputConfig(mode="archive")
    else:
        in_place = _prompt_yes_no(
            "Configure this repository in place?",
            default=False,
        )
        if in_place:
            output = OutputConfig(mode="inPlace")
        else:
            default_path = Path.cwd().parent / re.sub(
                r"[^a-z0-9]+",
                "-",
                project_name.lower(),
            ).strip("-")
            path = input(f"Destination [{default_path}]: ").strip()
            output = OutputConfig(mode="copy", path=path or str(default_path))

    if output.mode == "archive":
        apply_formatting = False
        verification = "none"
    else:
        apply_formatting = _prompt_yes_no("Apply Spotless formatting?", default=False)
        verification = input("Verification [none/narrow/full] (none): ").strip() or "none"
        if verification not in {"none", "narrow", "full"}:
            raise SetupError("verification must be none, narrow, or full")

    return SetupConfig(
        identity=IdentityConfig(
            package_name=package_name,
            project_name=project_name,
            application_id=application_id,
            display_name=display_name,
            plugin_alias=plugin_alias,
            author=author,
        ),
        output=output,
        starter=StarterConfig(
            remove_examples=remove_examples,
            ai_free=ai_free,
        ),
        project_settings=ProjectSettingsConfig(
            version_code=version_code,
            version_name=version_name,
            compile_sdk=compile_sdk,
            min_sdk=min_sdk,
            target_sdk=target_sdk,
            benchmark_min_sdk=benchmark_min_sdk,
            jvm_target=defaults.jvm_target,
            posts_backend_url=posts_backend_url,
        ),
        capabilities=frozenset(capabilities),
        validation=ValidationConfig(
            format=apply_formatting,
            level=verification,
        ),
    )


def _prompt_capabilities() -> set[str]:
    for index, capability in enumerate(CAPABILITIES, start=1):
        print(f"  {index:2}) {capability.title:<22} {capability.description}")
    raw = input("Capability numbers (comma-separated, empty for minimal): ").strip()
    if not raw:
        return set()
    try:
        indexes = {int(value.strip()) for value in raw.split(",")}
    except ValueError as error:
        raise SetupError("capability choices must be numbers") from error
    if any(index < 1 or index > len(CAPABILITIES) for index in indexes):
        raise SetupError("capability choice is out of range")
    return {CAPABILITIES[index - 1].id for index in indexes}


def _prompt_required(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        raise SetupError(f"{label} must not be empty")
    return value


def _prompt_default(label: str, default: object) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value or str(default)


def _prompt_integer(label: str, default: int | None) -> int:
    if default is None:
        raise SetupError(f"template default is missing for {label}")
    value = _prompt_default(label, default)
    try:
        return int(value)
    except ValueError as error:
        raise SetupError(f"{label} must be an integer") from error


def _has_cli_configuration(args: argparse.Namespace) -> bool:
    return any(
        (
            args.config,
            args.export_config,
            args.package_name,
            args.project_name,
            args.application_id,
            args.display_name,
            args.plugin_alias,
            args.author,
            args.version_code is not None,
            args.version_name,
            args.compile_sdk is not None,
            args.min_sdk is not None,
            args.target_sdk is not None,
            args.benchmark_min_sdk is not None,
            args.posts_backend_url,
            args.preset,
            args.capability,
            args.remove_examples is not None,
            args.ai_free is not None,
            args.output,
            args.in_place,
            args.archive,
            args.apply_formatting,
            args.verify,
            args.apply,
            args.force,
        ),
    )


def _prompt_yes_no(label: str, *, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    value = input(f"{label} {suffix}: ").strip().lower()
    if not value:
        return default
    if value in {"y", "yes"}:
        return True
    if value in {"n", "no"}:
        return False
    raise SetupError("answer must be yes or no")


def print_plan(plan: object) -> None:
    plan_value = plan.to_dict()
    print("\nSetup plan")
    print(f"  Source: {plan_value['sourceRoot']}")
    target = plan_value["targetRoot"] or plan_value["archiveName"]
    print(f"  Target: {target}")
    print(f"  Mode:   {plan_value['outputMode']}")
    print("\nOperations:")
    for operation in plan_value["operations"]:
        print(f"  • {operation}")
    print("\nCapabilities:")
    capabilities = plan_value["capabilities"]
    if not capabilities:
        print("  • Compose foundations only")
    for capability in capabilities:
        reason = f" — {capability['reason']}" if capability["reason"] else ""
        print(f"  • {capability['title']}{reason}")
    print(f"\nPlan digest: {plan_value['digest'][:16]}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SetupError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
