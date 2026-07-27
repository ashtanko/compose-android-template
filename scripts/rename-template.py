#!/usr/bin/env python3
"""Safely initialize or rename this Android project template."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape as xml_escape


PACKAGE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
PLUGIN_ALIAS_PATTERN = re.compile(r"^[a-z][a-z0-9]*$")
SKIPPED_DIRECTORY_NAMES = {
    ".git",
    ".gradle",
    ".idea",
    ".kotlin",
    "build",
}
KOTLIN_AND_JAVA_KEYWORDS = {
    "abstract",
    "actual",
    "annotation",
    "as",
    "assert",
    "boolean",
    "break",
    "byte",
    "by",
    "case",
    "catch",
    "char",
    "class",
    "companion",
    "const",
    "constructor",
    "continue",
    "crossinline",
    "data",
    "default",
    "do",
    "double",
    "dynamic",
    "else",
    "enum",
    "expect",
    "extends",
    "external",
    "false",
    "field",
    "final",
    "finally",
    "float",
    "for",
    "fun",
    "get",
    "goto",
    "if",
    "implements",
    "import",
    "in",
    "infix",
    "init",
    "inline",
    "instanceof",
    "int",
    "interface",
    "internal",
    "is",
    "it",
    "lateinit",
    "long",
    "native",
    "new",
    "noinline",
    "null",
    "object",
    "open",
    "operator",
    "out",
    "override",
    "package",
    "private",
    "protected",
    "public",
    "reified",
    "return",
    "sealed",
    "set",
    "short",
    "static",
    "strictfp",
    "super",
    "suspend",
    "switch",
    "synchronized",
    "tailrec",
    "this",
    "throw",
    "throws",
    "transient",
    "true",
    "try",
    "typealias",
    "typeof",
    "val",
    "var",
    "vararg",
    "void",
    "volatile",
    "when",
    "while",
}


class RenameError(RuntimeError):
    """An actionable template rename failure."""


@dataclass(frozen=True)
class Move:
    source: Path
    destination: Path


@dataclass(frozen=True)
class FileChange:
    path: Path
    original: bytes
    replacement: bytes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rename project packages, applicationId, convention plugins, "
            "display names, source folders, helper tooling, and optional author headers."
        ),
    )
    parser.add_argument("--package", required=True, dest="new_package")
    parser.add_argument("--name", required=True, dest="new_name")
    parser.add_argument("--plugin-alias")
    parser.add_argument("--author")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="list every file that would be or was changed",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow running with tracked or untracked working-tree changes",
    )
    return parser.parse_args()


def die(message: str) -> None:
    raise RenameError(message)


def info(message: str) -> None:
    print(f"\033[36m==>\033[0m {message}")


def note(message: str) -> None:
    print(f"    {message}")


def warn(message: str) -> None:
    print(f"\033[33mwarn:\033[0m {message}", file=sys.stderr)


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


def validate_single_line_xml_text(value: str, flag: str) -> None:
    if not value:
        die(f"{flag} must not be empty")
    if "\n" in value or "\r" in value:
        die(f"{flag} must be a single line")
    for character in value:
        codepoint = ord(character)
        if not (
            codepoint in (0x09,)
            or 0x20 <= codepoint <= 0xD7FF
            or 0xE000 <= codepoint <= 0xFFFD
            or 0x10000 <= codepoint <= 0x10FFFF
        ):
            die(f"{flag} contains a character that XML 1.0 cannot represent")


def validate_package(value: str) -> None:
    if not PACKAGE_PATTERN.fullmatch(value):
        die(
            "--package must be a lowercase dotted identifier with at least "
            f"two segments (got: {value})",
        )
    invalid_segment = next(
        (segment for segment in value.split(".") if segment in KOTLIN_AND_JAVA_KEYWORDS),
        None,
    )
    if invalid_segment is not None:
        die(f"--package contains the reserved keyword '{invalid_segment}'")


def current_plugin_aliases(catalog_path: Path, current_alias: str) -> set[str]:
    aliases: set[str] = set()
    in_plugins = False
    for line in catalog_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_plugins = stripped == "[plugins]"
            continue
        if not in_plugins or not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        top_level = re.split(r"[-_.]", key, maxsplit=1)[0]
        if top_level != current_alias:
            aliases.add(top_level)
    return aliases


def validate_inputs(
    args: argparse.Namespace,
    catalog_path: Path,
    current_alias: str,
) -> str:
    validate_package(args.new_package)
    validate_single_line_xml_text(args.new_name, "--name")

    derived_alias = args.new_package.rsplit(".", maxsplit=1)[-1].replace("_", "")
    plugin_alias = args.plugin_alias or derived_alias
    if not PLUGIN_ALIAS_PATTERN.fullmatch(plugin_alias):
        die(
            "--plugin-alias must start with a lowercase letter and contain "
            f"only lowercase letters and digits (got: {plugin_alias})",
        )
    if plugin_alias != current_alias:
        collision = plugin_alias in current_plugin_aliases(catalog_path, current_alias)
        if collision:
            die(
                f"--plugin-alias '{plugin_alias}' collides with an existing "
                "version-catalog plugin accessor",
            )

    if args.author is not None:
        validate_single_line_xml_text(args.author, "--author")
        if "*/" in args.author:
            die("--author must not contain '*/' because it appears in block comments")
        if "--" in args.author:
            die("--author must not contain '--' because it appears in XML comments")

    return plugin_alias


def load_identity(identity_path: Path) -> dict[str, str]:
    try:
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        die(f"cannot read template identity {identity_path}: {error}")
    required_keys = {
        "applicationPackage",
        "author",
        "buildLogicGroup",
        "buildLogicPackage",
        "codePackage",
        "displayName",
        "pluginAlias",
        "projectName",
    }
    missing_keys = sorted(required_keys.difference(identity))
    if missing_keys:
        die(f"template identity is missing: {', '.join(missing_keys)}")
    return identity


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


def kotlin_string_content(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
    )


def xml_text(value: str) -> str:
    return xml_escape(value, {'"': "&quot;", "'": "&apos;"})


def plugin_replacements(
    files: Iterable[Path],
    current_alias: str,
    new_alias: str,
) -> list[tuple[str, str]]:
    if current_alias == new_alias:
        return []

    replacements: set[tuple[str, str]] = set()
    plugin_key_pattern = re.compile(
        rf"(?m)^({re.escape(current_alias)})([-_.][A-Za-z0-9_.-]+)(?=\s*=)",
    )
    plugin_id_pattern = re.compile(
        rf'\bid\s*=\s*"({re.escape(current_alias)}\.[A-Za-z0-9_.-]+)"',
    )

    for path in files:
        if path.name not in {"libs.versions.toml", "build.gradle.kts"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for match in plugin_key_pattern.finditer(text):
            old_key = match.group(0).split("=", maxsplit=1)[0].strip()
            new_key = new_alias + old_key[len(current_alias) :]
            replacements.add((old_key, new_key))
            old_accessor = "libs.plugins." + re.sub(r"[-_.]+", ".", old_key)
            new_accessor = "libs.plugins." + re.sub(r"[-_.]+", ".", new_key)
            replacements.add((old_accessor, new_accessor))

        for match in plugin_id_pattern.finditer(text):
            old_id = match.group(1)
            replacements.add((old_id, new_alias + old_id[len(current_alias) :]))

    return sorted(replacements, key=lambda item: len(item[0]), reverse=True)


def text_replacements(
    identity: dict[str, str],
    new_package: str,
    new_build_logic_package: str,
    plugin_mappings: list[tuple[str, str]],
    author: str | None,
) -> list[tuple[str, str]]:
    mappings = [
        (identity["buildLogicGroup"], new_build_logic_package),
        (identity["buildLogicPackage"], new_build_logic_package),
        (identity["applicationPackage"], new_package),
        (identity["codePackage"], new_package),
        (
            identity["buildLogicPackage"].replace(".", "/"),
            new_build_logic_package.replace(".", "/"),
        ),
        (
            identity["applicationPackage"].replace(".", "/"),
            new_package.replace(".", "/"),
        ),
        (
            identity["codePackage"].replace(".", "/"),
            new_package.replace(".", "/"),
        ),
        *plugin_mappings,
    ]
    if author is not None:
        mappings.append((identity["author"], author))

    deduplicated: dict[str, str] = {}
    for old, new in mappings:
        if old and old != new:
            deduplicated[old] = new
    return sorted(deduplicated.items(), key=lambda item: len(item[0]), reverse=True)


def replacement_for_file(
    path: Path,
    text: str,
    identity: dict[str, str],
    new_name: str,
    mappings: list[tuple[str, str]],
) -> str:
    result = text
    for old, new in mappings:
        result = result.replace(old, new)

    suffix = path.suffix.lower()
    if suffix in {".kt", ".kts"}:
        escaped_name = kotlin_string_content(new_name)
    elif suffix == ".xml":
        escaped_name = xml_text(new_name)
    else:
        escaped_name = new_name

    display_values = {
        identity["displayName"],
        identity["projectName"],
    }
    for old_display_value in sorted(display_values, key=len, reverse=True):
        if old_display_value and old_display_value != new_name:
            result = result.replace(old_display_value, escaped_name)
    return result


def plan_file_changes(
    files: Iterable[Path],
    excluded_files: set[Path],
    identity: dict[str, str],
    new_name: str,
    mappings: list[tuple[str, str]],
) -> list[FileChange]:
    changes: list[FileChange] = []
    for path in files:
        if path in excluded_files or path.is_symlink():
            continue
        try:
            original = path.read_bytes()
            if b"\0" in original:
                continue
            text = original.decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        replacement_text = replacement_for_file(
            path,
            text,
            identity,
            new_name,
            mappings,
        )
        replacement = replacement_text.encode("utf-8")
        if replacement != original:
            changes.append(FileChange(path, original, replacement))
    return changes


def package_container_roots(repo_root: Path) -> Iterable[Path]:
    for directory, child_directories, _ in os.walk(repo_root):
        child_directories[:] = sorted(
            name for name in child_directories if name not in SKIPPED_DIRECTORY_NAMES
        )
        path = Path(directory)
        if (
            path.name in {"java", "kotlin", "reference"}
            and path.parent.parent.name == "src"
        ):
            yield path


def plan_moves(
    repo_root: Path,
    identity: dict[str, str],
    new_package: str,
    new_build_logic_package: str,
) -> list[Move]:
    path_mappings = {
        identity["codePackage"].replace(".", "/"): new_package.replace(".", "/"),
        identity["applicationPackage"].replace(".", "/"): new_package.replace(".", "/"),
        identity["buildLogicPackage"].replace(".", "/"): new_build_logic_package.replace(
            ".",
            "/",
        ),
    }
    planned: dict[Path, Path] = {}
    package_roots = list(package_container_roots(repo_root))

    for old_subpath, new_subpath in path_mappings.items():
        for package_root in package_roots:
            source_root = package_root / old_subpath
            destination_root = package_root / new_subpath
            if not source_root.is_dir() or source_root == destination_root:
                continue
            for directory, _, filenames in os.walk(source_root):
                directory_path = Path(directory)
                for filename in sorted(filenames):
                    source = directory_path / filename
                    destination = destination_root / source.relative_to(source_root)
                    previous_destination = planned.get(source)
                    if previous_destination is not None and previous_destination != destination:
                        die(f"ambiguous destination for {source}")
                    planned[source] = destination

    moves = [Move(source, destination) for source, destination in planned.items()]
    moves.sort(key=lambda move: str(move.source))
    validate_move_plan(moves)
    return moves


def validate_move_plan(moves: list[Move]) -> None:
    destinations: dict[Path, Path] = {}
    for move in moves:
        previous_source = destinations.get(move.destination)
        if previous_source is not None and previous_source != move.source:
            die(
                f"multiple source files would overwrite {move.destination}: "
                f"{previous_source} and {move.source}",
            )
        destinations[move.destination] = move.source
        if move.destination.exists():
            die(f"rename target already exists: {move.destination}")


def updated_identity(
    identity: dict[str, str],
    new_package: str,
    new_name: str,
    new_build_logic_package: str,
    plugin_alias: str,
    author: str | None,
) -> bytes:
    result = dict(identity)
    result.update(
        {
            "applicationPackage": new_package,
            "buildLogicGroup": new_build_logic_package,
            "buildLogicPackage": new_build_logic_package,
            "codePackage": new_package,
            "displayName": new_name,
            "pluginAlias": plugin_alias,
            "projectName": new_name,
        },
    )
    if author is not None:
        result["author"] = author
    return (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, content: bytes, mode: int) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def apply_transaction(
    changes: list[FileChange],
    moves: list[Move],
    identity_path: Path,
    identity_replacement: bytes,
) -> None:
    changed_modes = {change.path: change.path.stat().st_mode for change in changes}
    identity_original = identity_path.read_bytes()
    identity_mode = identity_path.stat().st_mode
    completed_moves: list[Move] = []
    created_directories: set[Path] = set()

    def interrupt_handler(signum: int, _frame: object) -> None:
        raise KeyboardInterrupt(f"received signal {signum}")

    previous_sigint = signal.signal(signal.SIGINT, interrupt_handler)
    previous_sigterm = signal.signal(signal.SIGTERM, interrupt_handler)
    try:
        for change in changes:
            atomic_write(change.path, change.replacement, changed_modes[change.path])

        for move in moves:
            missing_parents: list[Path] = []
            parent = move.destination.parent
            while not parent.exists():
                missing_parents.append(parent)
                parent = parent.parent
            move.destination.parent.mkdir(parents=True, exist_ok=True)
            created_directories.update(missing_parents)
            shutil.move(move.source, move.destination)
            completed_moves.append(move)

        atomic_write(identity_path, identity_replacement, identity_mode)
    except BaseException:
        for move in reversed(completed_moves):
            if move.destination.exists() and not move.source.exists():
                move.source.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(move.destination, move.source)
        for change in changes:
            atomic_write(change.path, change.original, changed_modes[change.path])
        atomic_write(identity_path, identity_original, identity_mode)
        for directory in sorted(created_directories, key=lambda path: len(path.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
        signal.signal(signal.SIGTERM, previous_sigterm)


def prune_empty_source_directories(moves: Iterable[Move]) -> None:
    directories: set[Path] = set()
    for move in moves:
        directory = move.source.parent
        while directory.name not in {"java", "kotlin", "reference"}:
            directories.add(directory)
            directory = directory.parent
    for directory in sorted(directories, key=lambda path: len(path.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


def display_plan(
    repo_root: Path,
    changes: list[FileChange],
    moves: list[Move],
    dry_run: bool,
    verbose: bool,
) -> None:
    verb = "would rewrite" if dry_run else "rewriting"
    info(f"{verb} {len(changes)} text file(s)")
    if verbose:
        for change in changes:
            note(str(change.path.relative_to(repo_root)))

    move_verb = "would move" if dry_run else "moving"
    info(f"{move_verb} {len(moves)} source file(s)")
    if verbose:
        for move in moves:
            note(
                f"{move.source.relative_to(repo_root)} -> "
                f"{move.destination.relative_to(repo_root)}",
            )


def main() -> int:
    args = parse_args()
    scripts_directory = Path(__file__).resolve().parent
    repo_root = scripts_directory.parent
    identity_path = scripts_directory / "template-identity.json"
    wrapper_path = scripts_directory / "rename-template.sh"
    implementation_path = Path(__file__).resolve()

    identity = load_identity(identity_path)
    in_git = is_git_worktree(repo_root)
    if in_git and not args.force:
        status = run_git(
            repo_root,
            "status",
            "--porcelain",
            "--untracked-files=all",
        ).stdout
        if status.strip():
            die("working tree has uncommitted changes; commit/stash first or pass --force")

    catalog_path = repo_root / "gradle" / "libs.versions.toml"
    plugin_alias = validate_inputs(args, catalog_path, identity["pluginAlias"])
    new_build_logic_package = f"{args.new_package}.buildlogic"
    files = repository_files(repo_root, in_git)
    plugin_mappings = plugin_replacements(
        files,
        identity["pluginAlias"],
        plugin_alias,
    )
    mappings = text_replacements(
        identity,
        args.new_package,
        new_build_logic_package,
        plugin_mappings,
        args.author,
    )
    changes = plan_file_changes(
        files,
        {wrapper_path, implementation_path, identity_path},
        identity,
        args.new_name,
        mappings,
    )
    moves = plan_moves(
        repo_root,
        identity,
        args.new_package,
        new_build_logic_package,
    )
    identity_replacement = updated_identity(
        identity,
        args.new_package,
        args.new_name,
        new_build_logic_package,
        plugin_alias,
        args.author,
    )

    info(f"repo root:      {repo_root}")
    info(f"new package:    {args.new_package}")
    info(f"new name:       {args.new_name}")
    info(f"plugin alias:   {plugin_alias}")
    info(f"build-logic:    {new_build_logic_package}")
    if args.author is None:
        note("author rewrite: skipped (pass --author to enable)")
    else:
        info(f"author:         {args.author}")
    if args.dry_run:
        warn("DRY RUN — no files will be modified")

    display_plan(repo_root, changes, moves, args.dry_run, args.verbose)
    if args.dry_run:
        warn("this was a DRY RUN — re-run without --dry-run to apply")
        return 0

    apply_transaction(changes, moves, identity_path, identity_replacement)
    prune_empty_source_directories(moves)

    info("done.")
    commit_message = shlex.quote(f"Initialize project: {args.new_name}")
    print(
        f"""
next steps:
  1. review changes:         git status && git diff
  2. apply formatting:       ./gradlew spotlessApply
  3. run full verification:  make verify
  4. commit:                 git add -A && git commit -m {commit_message}
""",
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RenameError as error:
        print(f"\033[31merror:\033[0m {error}", file=sys.stderr)
        raise SystemExit(1) from None
