#!/usr/bin/env python3
"""Validate that this project was fully renamed away from the template.

Run this after ``scripts/rename-template.sh``. It confirms that no original
template identity values remain in the working tree, that Kotlin/Java source
folders match the new package, that ``scripts/template-identity.json`` is
internally consistent, and that the touched Android string resources still
parse as XML.

The check reports every problem it finds and exits non-zero when the rename is
incomplete, so it is safe to run in CI after bootstrapping a new project.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as element_tree
from pathlib import Path
from typing import Iterable

# The pristine identity shipped with this template. rename-template.sh rewrites
# every tracked file that mentions these values, so a fully renamed project must
# contain none of the ones the user actually changed. This file is deliberately
# excluded from the rename rewrite (see rename-template.py) so these anchors
# survive the rename and can be compared against afterwards.
BASELINE_IDENTITY = {
    "applicationPackage": "dev.shtanko.template",
    "author": "ashtanko (Oleksii Shtanko)",
    "buildLogicGroup": "dev.shtanko.androidlab.buildlogic",
    "buildLogicPackage": "dev.shtanko.androidlab",
    "codePackage": "app.template",
    "displayName": "Compose Android Template",
    "pluginAlias": "androidlab",
    "projectName": "Android Template",
}

REQUIRED_IDENTITY_KEYS = set(BASELINE_IDENTITY)

SKIPPED_DIRECTORY_NAMES = {
    ".git",
    ".gradle",
    ".idea",
    ".kotlin",
    "build",
}

SOURCE_ROOT_NAMES = {"java", "kotlin", "reference"}
PACKAGE_PATH_KEYS = ("applicationPackage", "codePackage", "buildLogicPackage")


class ValidationError(RuntimeError):
    """A precondition failure that stops validation before checks can run."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that this project was fully renamed from the template: "
            "no stale identity values, matching source folders, a consistent "
            "template-identity.json, and valid string resources."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="list each check as it runs and every file scanned",
    )
    return parser.parse_args()


def info(message: str) -> None:
    print(f"\033[36m==>\033[0m {message}")


def note(message: str) -> None:
    print(f"    {message}")


def ok(message: str) -> None:
    print(f"\033[32mok:\033[0m {message}")


def warn(message: str) -> None:
    print(f"\033[33mwarn:\033[0m {message}", file=sys.stderr)


def die(message: str) -> None:
    raise ValidationError(message)


def run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )


def is_git_worktree(repo_root: Path) -> bool:
    return run_git(repo_root, "rev-parse", "--is-inside-work-tree").returncode == 0


def path_is_skipped(path: Path) -> bool:
    return any(part in SKIPPED_DIRECTORY_NAMES for part in path.parts)


def repository_files(repo_root: Path, in_git: bool) -> list[Path]:
    if in_git:
        result = run_git(
            repo_root,
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        )
        if result.returncode != 0:
            die("could not enumerate repository files with git")
        relative_paths = [
            Path(os.fsdecode(raw_path))
            for raw_path in result.stdout.split(b"\0")
            if raw_path
        ]
        return sorted(
            repo_root / path
            for path in relative_paths
            if not path_is_skipped(path) and (repo_root / path).is_file()
        )

    files: list[Path] = []
    for directory, child_directories, filenames in os.walk(repo_root):
        child_directories[:] = sorted(
            name for name in child_directories if name not in SKIPPED_DIRECTORY_NAMES
        )
        directory_path = Path(directory)
        files.extend(directory_path / filename for filename in sorted(filenames))
    return files


def load_identity(identity_path: Path) -> dict[str, str]:
    try:
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        die(f"cannot read template identity {identity_path}: {error}")
    missing_keys = sorted(REQUIRED_IDENTITY_KEYS.difference(identity))
    if missing_keys:
        die(f"template identity is missing: {', '.join(missing_keys)}")
    return identity


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def check_identity_consistency(
    identity: dict[str, str],
    failures: list[str],
) -> None:
    application_package = identity["applicationPackage"]
    if application_package == BASELINE_IDENTITY["applicationPackage"]:
        die(
            "template-identity.json still uses the template package "
            f"'{application_package}'; run scripts/rename-template.sh before validating",
        )

    if identity["codePackage"] != application_package:
        failures.append(
            f"codePackage '{identity['codePackage']}' does not match applicationPackage "
            f"'{application_package}'; the rename looks incomplete",
        )

    expected_build_logic = f"{application_package}.buildlogic"
    for key in ("buildLogicPackage", "buildLogicGroup"):
        if identity[key] != expected_build_logic:
            failures.append(
                f"{key} '{identity[key]}' does not match the expected "
                f"'{expected_build_logic}'; the rename looks incomplete",
            )


def plugin_alias_tokens(old_alias: str) -> list[str]:
    # rename-template.sh only guarantees rewriting the plugin key, accessor, and
    # id forms of the alias (not bare prose mentions), so validate exactly those
    # forms — mirroring the contract asserted in check-template-tools.sh.
    return [
        f"{old_alias}.android",
        f"{old_alias}.jvm",
        f"{old_alias}.hilt",
        f"{old_alias}.kotlin",
        f"{old_alias}.spotless",
        f"{old_alias}-",
        f"libs.plugins.{old_alias}",
    ]


def build_stale_needles(identity: dict[str, str]) -> list[tuple[str, str]]:
    needles: list[tuple[str, str]] = []
    for key, baseline_value in sorted(BASELINE_IDENTITY.items()):
        if key == "pluginAlias":
            continue
        new_value = identity[key]
        if new_value == baseline_value:
            # The user chose to keep this value (for example, an unchanged
            # --author), so its presence is expected rather than stale.
            continue
        if baseline_value in new_value:
            # A superstring rename (the new value contains the old one) makes a
            # plain substring scan ambiguous, so skip this anchor.
            continue
        needles.append((key, baseline_value))

    old_alias = BASELINE_IDENTITY["pluginAlias"]
    new_alias = identity["pluginAlias"]
    if new_alias != old_alias and old_alias not in new_alias:
        needles.extend(("pluginAlias", token) for token in plugin_alias_tokens(old_alias))
    return needles


def scan_stale_values(
    repo_root: Path,
    files: Iterable[Path],
    identity: dict[str, str],
    excluded: set[Path],
    failures: list[str],
) -> None:
    needles = build_stale_needles(identity)
    if not needles:
        return
    for path in files:
        if path in excluded:
            continue
        text = read_text(path)
        if text is None:
            continue
        for key, value in needles:
            if value in text:
                failures.append(
                    f"stale template {key} '{value}' still present in "
                    f"{path.relative_to(repo_root)}",
                )


def scan_stale_source_dirs(
    repo_root: Path,
    identity: dict[str, str],
    failures: list[str],
) -> None:
    old_paths = [
        tuple(BASELINE_IDENTITY[key].split("."))
        for key in PACKAGE_PATH_KEYS
        if identity[key] != BASELINE_IDENTITY[key]
    ]
    if not old_paths:
        return

    for directory, child_directories, _ in os.walk(repo_root):
        child_directories[:] = sorted(
            name for name in child_directories if name not in SKIPPED_DIRECTORY_NAMES
        )
        relative_parts = Path(directory).relative_to(repo_root).parts
        try:
            source_index = relative_parts.index("src")
        except ValueError:
            continue
        if (
            len(relative_parts) <= source_index + 2
            or relative_parts[source_index + 2] not in SOURCE_ROOT_NAMES
        ):
            continue
        for old_path in old_paths:
            if (
                len(relative_parts) >= len(old_path)
                and relative_parts[-len(old_path) :] == old_path
            ):
                failures.append(
                    "stale template source directory "
                    f"{Path(directory).relative_to(repo_root)}",
                )


def check_string_resources(
    repo_root: Path,
    files: Iterable[Path],
    failures: list[str],
) -> None:
    for path in files:
        if path.name != "strings.xml":
            continue
        try:
            element_tree.parse(path)
        except (OSError, element_tree.ParseError) as error:
            failures.append(f"invalid XML in {path.relative_to(repo_root)}: {error}")


def main() -> int:
    args = parse_args()
    scripts_directory = Path(__file__).resolve().parent
    repo_root = scripts_directory.parent
    identity_path = scripts_directory / "template-identity.json"
    excluded = {
        scripts_directory / "validate-rename.py",
        scripts_directory / "validate-rename.sh",
    }

    identity = load_identity(identity_path)
    in_git = is_git_worktree(repo_root)
    files = repository_files(repo_root, in_git)

    info(f"repo root:    {repo_root}")
    info(f"package:      {identity['applicationPackage']}")
    info(f"display name: {identity['displayName']}")
    if args.verbose:
        note(f"scanning {len(files)} tracked file(s)")

    failures: list[str] = []
    check_identity_consistency(identity, failures)
    if args.verbose:
        note("checked template-identity.json consistency")
    scan_stale_values(repo_root, files, identity, excluded, failures)
    if args.verbose:
        note("scanned tracked files for stale template identity values")
    scan_stale_source_dirs(repo_root, identity, failures)
    if args.verbose:
        note("scanned source sets for stale package directories")
    check_string_resources(repo_root, files, failures)
    if args.verbose:
        note("validated Android string resources")

    if failures:
        for failure in failures:
            print(f"\033[31merror:\033[0m {failure}", file=sys.stderr)
        print(
            f"\nRename validation failed with {len(failures)} finding(s).",
            file=sys.stderr,
        )
        print(
            "Re-run scripts/rename-template.sh (or fix the files above) so no "
            "template identity remains, then validate again.",
            file=sys.stderr,
        )
        return 1

    ok("project rename validated; no template identity remains")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as error:
        print(f"\033[31merror:\033[0m {error}", file=sys.stderr)
        raise SystemExit(1) from None
