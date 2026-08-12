"""Planning and transactional application for project setup."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from datetime import date
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Match
from xml.sax.saxutils import escape as xml_escape

from .model import (
    CAPABILITY_BY_ID,
    ProjectSettingsConfig,
    SetupConfig,
    derived_plugin_alias,
    validate_config,
    with_resolved_capabilities,
    with_resolved_project_settings,
)


SKIPPED_DIRECTORIES = {
    ".git",
    ".gradle",
    ".idea",
    ".kotlin",
    "__pycache__",
    "build",
}
SKIPPED_LOCAL_FILES = {"local.properties", "key.properties"}
SOURCE_MANIFEST_PATH = Path("scripts/setup_wizard/source-manifest.txt")
SCREENSHOT_VERIFICATION_TASKS = (
    "validateDebugScreenshotTest",
    "verifyRoborazziDebug",
)
AI_TOOLING_PATHS = (
    ".agents",
    ".claude",
    "AGENTS.md",
    "CLAUDE.md",
    "skills-lock.json",
)
EXAMPLE_MODULES = (
    "feature/home",
    "feature/posts",
    "core/database",
    "library-android",
    "library-kotlin",
)
EXAMPLE_SETTINGS = (
    ':core:database',
    ':feature:home',
    ':feature:posts:domain',
    ':feature:posts:data',
    ':feature:posts:presentation',
    ':library-android',
    ':library-kotlin',
)
APP_DEPENDENCY_CAPABILITIES = {
    "libs.androidx.runtime.tracing": "baseline_profiles",
    "libs.androidx.tracing.ktx": "baseline_profiles",
    "libs.androidx.navigation3.runtime": "navigation",
    "libs.androidx.navigation3.ui": "navigation",
    "libs.androidx.material3.navigation3": "navigation",
    "libs.androidx.compose.material3.adaptive": "adaptive_ui",
    "libs.androidx.compose.material3.adaptive.layout": "adaptive_ui",
    "libs.androidx.compose.material3.adaptive.navigation": "adaptive_ui",
    "libs.androidx.compose.material3.adaptive.navigationSuite": "adaptive_ui",
    "libs.androidx.compose.materialWindow": "adaptive_ui",
    "libs.androidx.compose.icons.extended": "visual_extras",
    "libs.androidx.ui.text.google.fonts": "visual_extras",
    "libs.arch.core.test": "test_tooling",
    "baselineProfile(project": "baseline_profiles",
    "libs.paging.runtime": "paging",
    "libs.paging.compose": "paging",
    "libs.generativeai": "generative_ai",
    "libs.kotlinx.coroutines.android": "coroutines",
    "libs.kotlinx.coroutines.core": "coroutines",
    "libs.kotlinx.serialization": "serialization",
    "libs.kotlinx.coroutines.test": "coroutines",
    "libs.kotlinx.coroutines.debug": "test_tooling",
    "libs.coil.kt": "coil",
    "libs.coil.kt.compose": "coil",
    "libs.coil.kt.svg": "coil",
    "libs.hilt.compiler": "hilt",
    "libs.hilt.android.testing": "hilt",
    "libs.accompanist.adaptive": "adaptive_ui",
    "libs.accompanist.permissions": "permissions",
    "libs.androidx.window": "adaptive_ui",
    "libs.androidx.window.core": "adaptive_ui",
    "libs.room.paging": "room_and_paging",
    "libs.jacoco.core": "coverage",
    "libs.square.okhttp": "networking",
    "libs.square.okhttp.logging": "networking",
    "libs.square.okhttp.mockwebserver": "networking",
    "libs.square.retrofit.core": "networking",
    "libs.skydoves.sandwich.retrofit": "networking",
    "libs.square.retrofit.kotlin.serialization": "networking",
    "libs.square.turbine": "test_tooling",
    "libs.mockito": "test_tooling",
    "libs.mockito.kotlin2": "test_tooling",
    "libs.mockk.kotlin": "test_tooling",
    "libs.mockk.android": "test_tooling",
    "libs.robolectric.robolectric": "test_tooling",
    "libs.androidx.espresso.core": "test_tooling",
}
APP_PLUGIN_CAPABILITIES = {
    ".android.application.baselineprofile)": "baseline_profiles",
    ".android.application.jacoco)": "coverage",
    ".android.compose.screenshot)": "screenshots",
    ".android.roborazzi)": "screenshots",
    ".android.room)": "room",
    ".hilt)": "hilt",
    "plugins.serialization": "serialization",
    "plugins.kover": "coverage",
    "plugins.sonarqube": "coverage",
}


class SetupError(RuntimeError):
    """An actionable setup failure."""


@dataclass(frozen=True)
class SetupPlan:
    source_root: Path
    target_root: Path | None
    config: SetupConfig
    reasons: dict[str, str]
    operations: tuple[str, ...]
    digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "digest": self.digest,
            "sourceRoot": str(self.source_root),
            "targetRoot": (
                str(self.target_root)
                if self.target_root is not None
                else None
            ),
            "archiveName": archive_name(self.config),
            "outputMode": self.config.output.mode,
            "capabilities": [
                {
                    "id": capability_id,
                    "title": CAPABILITY_BY_ID[capability_id].title,
                    "reason": self.reasons.get(capability_id),
                }
                for capability_id in sorted(self.config.capabilities)
            ],
            "operations": list(self.operations),
            "config": self.config.to_dict(),
        }


def default_source_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_plan(
    config: SetupConfig,
    *,
    source_root: Path | None = None,
) -> SetupPlan:
    validate_config(config)
    resolved_config, reasons = with_resolved_capabilities(config)
    source = (source_root or default_source_root()).resolve()
    identity_path = source / "scripts" / "template-identity.json"
    rename_path = source / "scripts" / "rename-template.py"
    if not identity_path.is_file() or not rename_path.is_file():
        raise SetupError(f"{source} is not a supported template repository")
    try:
        resolved_config = with_resolved_project_settings(
            resolved_config,
            read_project_settings(source),
        )
    except ValueError as error:
        raise SetupError(str(error)) from error
    _validate_plugin_alias_collision(source, resolved_config)

    if resolved_config.output.mode == "copy":
        raw_target = Path(resolved_config.output.path or "")
        target = raw_target.expanduser()
        if not target.is_absolute():
            target = (Path.cwd() / target).resolve()
        else:
            target = target.resolve()
        if target == source or _is_relative_to(target, source):
            raise SetupError("copy destination must be outside the template repository")
    elif resolved_config.output.mode == "inPlace":
        target = source
    else:
        target = None

    identity_bytes = identity_path.read_bytes()
    if resolved_config.output.mode == "copy":
        output_operation = f"Copy tracked template files to {target}"
    elif resolved_config.output.mode == "inPlace":
        output_operation = f"Configure the current repository at {source}"
    else:
        output_operation = (
            f"Prepare {archive_name(resolved_config)} as a browser download"
        )
    operations = [
        output_operation,
        (
            f"Rename project to “{resolved_config.identity.project_name}” "
            f"with package {resolved_config.identity.package_name}"
        ),
        (
            f"Set application ID {resolved_config.identity.application_id} and "
            f"display name “{resolved_config.identity.display_name}”"
        ),
        (
            "Configure app version and Android SDK levels from the resolved "
            "project settings"
        ),
        f"Enable {len(resolved_config.capabilities)} optional capability group(s)",
    ]
    if resolved_config.project_settings.posts_backend_url is not None:
        operations.append("Configure the retained Posts example backend URL")
    if resolved_config.starter.remove_examples:
        operations.append(
            "Remove example features and sample libraries; generate a minimal Compose starter",
        )
        if "navigation" not in resolved_config.capabilities:
            operations.append("Remove the unused core navigation module")
        if "baseline_profiles" not in resolved_config.capabilities:
            operations.append("Remove the benchmark module and baseline-profile wiring")
    if resolved_config.starter.ai_free:
        operations.append(
            "Remove coding-agent guidance and generative-AI integration",
        )
    if resolved_config.validation.format:
        operations.append("Apply Spotless formatting")
    if resolved_config.validation.level != "none":
        operations.append(
            f"Run {resolved_config.validation.level} generated-project verification",
        )

    digest_payload = {
        "config": resolved_config.to_dict(),
        "source": str(source),
        "identity": hashlib.sha256(identity_bytes).hexdigest(),
        "sourceState": _source_fingerprint(source),
        "operations": operations,
    }
    digest = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True).encode("utf-8"),
    ).hexdigest()
    return SetupPlan(
        source_root=source,
        target_root=target,
        config=resolved_config,
        reasons=reasons,
        operations=tuple(operations),
        digest=digest,
    )


def apply_plan(
    plan: SetupPlan,
    *,
    expected_digest: str | None = None,
    force: bool = False,
) -> Path:
    current_plan = build_plan(plan.config, source_root=plan.source_root)
    if current_plan.digest != plan.digest:
        raise SetupError("the repository or configuration changed; preview the plan again")
    if expected_digest is not None and expected_digest != plan.digest:
        raise SetupError("plan approval is stale; preview the plan again")

    if plan.config.output.mode == "copy":
        result = _apply_to_copy(plan)
    elif plan.config.output.mode == "inPlace":
        result = _apply_in_place(plan, force=force)
    else:
        raise SetupError("archive plans must be generated as a ZIP download")

    _run_selected_validation(result, plan.config)
    return result


def _apply_to_copy(plan: SetupPlan) -> Path:
    destination = plan.target_root
    if destination is None:
        raise SetupError("copy plan is missing its destination")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and any(destination.iterdir()):
        raise SetupError(f"destination is not empty: {destination}")

    staging = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.setup-",
            dir=destination.parent,
        ),
    )
    published = False
    try:
        _prepare_project(plan.source_root, staging, plan.config)
        if destination.exists():
            destination.rmdir()
        os.replace(staging, destination)
        published = True
        return destination
    except (OSError, subprocess.SubprocessError) as error:
        raise SetupError(f"could not create project copy: {error}") from error
    finally:
        if not published:
            shutil.rmtree(staging, ignore_errors=True)


def create_archive(
    plan: SetupPlan,
    *,
    expected_digest: str | None = None,
) -> tuple[bytes, str]:
    if plan.config.output.mode != "archive":
        raise SetupError("only archive plans can be downloaded")
    current_plan = build_plan(plan.config, source_root=plan.source_root)
    if current_plan.digest != plan.digest:
        raise SetupError("the repository or configuration changed; preview the plan again")
    if expected_digest is not None and expected_digest != plan.digest:
        raise SetupError("plan approval is stale; preview the plan again")

    project_directory = archive_name(plan.config).removesuffix(".zip")
    try:
        with tempfile.TemporaryDirectory(prefix="project-archive-") as temporary:
            project_root = Path(temporary) / project_directory
            project_root.mkdir()
            _prepare_project(plan.source_root, project_root, plan.config)
            return (
                _zip_project(project_root, project_directory),
                f"{project_directory}.zip",
            )
    except (OSError, subprocess.SubprocessError) as error:
        raise SetupError(f"could not create project archive: {error}") from error


def archive_name(config: SetupConfig) -> str:
    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        config.identity.project_name.lower(),
    ).strip("-")
    return f"{slug or 'android-project'}.zip"


def _prepare_project(
    source_root: Path,
    target_root: Path,
    config: SetupConfig,
) -> None:
    for relative_path in _tracked_files(source_root):
        source = source_root / relative_path
        target = target_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            target.symlink_to(os.readlink(source))
        else:
            shutil.copy2(source, target)
    _configure_repository(target_root, config)
    _write_source_manifest(target_root, _walk_files(target_root))


def _zip_project(project_root: Path, project_directory: str) -> bytes:
    archive = io.BytesIO()
    with zipfile.ZipFile(
        archive,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as output:
        for path in sorted(
            (candidate for candidate in project_root.rglob("*") if not candidate.is_dir()),
        ):
            relative_path = path.relative_to(project_root)
            archive_path = f"{project_directory}/{relative_path.as_posix()}"
            info = zipfile.ZipInfo(
                archive_path,
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            if path.is_symlink():
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                content = os.fsencode(os.readlink(path))
            else:
                mode = stat.S_IMODE(path.stat().st_mode)
                info.external_attr = (stat.S_IFREG | mode) << 16
                content = path.read_bytes()
            output.writestr(info, content)
    return archive.getvalue()


def _apply_in_place(plan: SetupPlan, *, force: bool) -> Path:
    if _git_is_dirty(plan.source_root) and not force:
        raise SetupError(
            "working tree has uncommitted changes; commit/stash first or pass --force",
        )
    with _RepositorySnapshot(plan.source_root):
        _configure_repository(plan.source_root, plan.config)
    return plan.source_root


class _RepositorySnapshot:
    """Restore all non-ignored repository files if a setup operation fails."""

    def __init__(self, root: Path):
        self.root = root
        self.temporary: tempfile.TemporaryDirectory[str] | None = None
        self.backup_root: Path | None = None
        self.original_paths: set[Path] = set()

    def __enter__(self) -> "_RepositorySnapshot":
        self.temporary = tempfile.TemporaryDirectory(prefix="project-setup-backup-")
        self.backup_root = Path(self.temporary.name)
        self.original_paths = set(_repository_files(self.root))
        for relative_path in self.original_paths:
            source = self.root / relative_path
            target = self.backup_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                target.symlink_to(os.readlink(source))
            else:
                shutil.copy2(source, target)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object,
    ) -> bool:
        try:
            if exception is not None:
                self._restore()
        finally:
            if self.temporary is not None:
                self.temporary.cleanup()
        return False

    def _restore(self) -> None:
        if self.backup_root is None:
            return
        current_paths = set(_repository_files(self.root))
        for relative_path in sorted(
            current_paths.difference(self.original_paths),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            path = self.root / relative_path
            if path.is_file() or path.is_symlink():
                path.unlink()
        for relative_path in self.original_paths:
            source = self.backup_root / relative_path
            target = self.root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() or target.is_symlink():
                target.unlink()
            if source.is_symlink():
                target.symlink_to(os.readlink(source))
            else:
                shutil.copy2(source, target)
        _prune_empty_directories(self.root)


def _configure_repository(root: Path, config: SetupConfig) -> None:
    _run_rename(root, config)
    _configure_project_settings(root, config)
    _configure_modules_and_dependencies(root, config)
    if config.starter.remove_examples:
        _install_minimal_starter(root, config)
    if config.starter.ai_free:
        _configure_ai_free_project(root)
    _sort_kotlin_imports(root)
    _neutralize_missing_markdown_links(root)


def read_project_settings(root: Path) -> ProjectSettingsConfig:
    """Read the template-owned defaults used to resolve partial configurations."""
    identity = json.loads(
        _read_required_text(root / "scripts" / "template-identity.json"),
    )
    app_build = _read_required_text(root / "app" / "build.gradle.kts")
    catalog = _read_required_text(root / "gradle" / "libs.versions.toml")
    posts_network_path = _posts_network_module(root, identity["codePackage"])
    posts_backend_url = None
    if posts_network_path.is_file():
        posts_backend_url = _unescape_kotlin_string(
            _required_match(
                _read_required_text(posts_network_path),
                r'(?m)^\s*private const val POSTS_BASE_URL\s*=\s*"((?:\\.|[^"\\])*)"\s*$',
                "Posts example backend URL",
            ),
        )
    return ProjectSettingsConfig(
        version_code=int(
            _required_match(
                app_build,
                r"(?m)^\s*versionCode\s*=\s*(\d+)\s*$",
                "app versionCode",
            ),
        ),
        version_name=_unescape_kotlin_string(
            _required_match(
                app_build,
                r'(?m)^\s*versionName\s*=\s*"((?:\\.|[^"\\])*)"\s*$',
                "app versionName",
            ),
        ),
        compile_sdk=_catalog_integer(catalog, "compileSdk"),
        min_sdk=_catalog_integer(catalog, "minSdk"),
        target_sdk=_catalog_integer(catalog, "targetSdk"),
        benchmark_min_sdk=_catalog_integer(catalog, "benchmarkMinSdk"),
        jvm_target=_catalog_integer(catalog, "jvmTarget"),
        posts_backend_url=posts_backend_url,
    )


def _configure_project_settings(root: Path, config: SetupConfig) -> None:
    identity = config.identity
    project = config.project_settings
    required_values = {
        "applicationId": identity.application_id,
        "displayName": identity.display_name,
        "versionCode": project.version_code,
        "versionName": project.version_name,
        "compileSdk": project.compile_sdk,
        "minSdk": project.min_sdk,
        "targetSdk": project.target_sdk,
        "benchmarkMinSdk": project.benchmark_min_sdk,
        "jvmTarget": project.jvm_target,
    }
    missing = sorted(key for key, value in required_values.items() if value is None)
    if missing:
        raise SetupError(
            f"project settings were not fully resolved: {', '.join(missing)}",
        )

    app_build_path = root / "app" / "build.gradle.kts"
    app_build = _read_required_text(app_build_path)
    app_build = _replace_once(
        app_build,
        r'(?m)^(\s*applicationId\s*=\s*")((?:\\.|[^"\\])*)("\s*)$',
        lambda match: (
            f"{match.group(1)}{_kotlin_string(identity.application_id or '')}"
            f"{match.group(3)}"
        ),
        "applicationId",
    )
    app_build = _replace_once(
        app_build,
        r"(?m)^(\s*versionCode\s*=\s*)\d+(\s*)$",
        lambda match: f"{match.group(1)}{project.version_code}{match.group(2)}",
        "versionCode",
    )
    app_build = _replace_once(
        app_build,
        r'(?m)^(\s*versionName\s*=\s*")((?:\\.|[^"\\])*)("\s*)$',
        lambda match: (
            f"{match.group(1)}{_kotlin_string(project.version_name or '')}"
            f"{match.group(3)}"
        ),
        "versionName",
    )
    app_build_path.write_text(app_build, encoding="utf-8")

    catalog_path = root / "gradle" / "libs.versions.toml"
    catalog = _read_required_text(catalog_path)
    for key, value in (
        ("jvmTarget", project.jvm_target),
        ("compileSdk", project.compile_sdk),
        ("minSdk", project.min_sdk),
        ("benchmarkMinSdk", project.benchmark_min_sdk),
        ("targetSdk", project.target_sdk),
    ):
        catalog = _replace_once(
            catalog,
            rf'(?m)^({re.escape(key)}\s*=\s*")[^"\n]*(".*)$',
            lambda match, setting=value: (
                f"{match.group(1)}{setting}{match.group(2)}"
            ),
            key,
        )
    catalog_path.write_text(catalog, encoding="utf-8")

    strings_path = root / "app" / "src" / "main" / "res" / "values" / "strings.xml"
    strings = _read_required_text(strings_path)
    strings = _replace_once(
        strings,
        r'(?s)(<string\s+name="app_name"[^>]*>).*?(</string>)',
        lambda match: (
            f"{match.group(1)}{xml_escape(identity.display_name or '')}"
            f"{match.group(2)}"
        ),
        "app_name resource",
    )
    strings_path.write_text(strings, encoding="utf-8")

    identity_path = root / "scripts" / "template-identity.json"
    identity_value = json.loads(_read_required_text(identity_path))
    identity_value["applicationPackage"] = identity.application_id
    identity_value["displayName"] = identity.display_name
    identity_path.write_text(
        json.dumps(identity_value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    benchmark_config = _benchmark_config(root, config.identity.package_name)
    if benchmark_config.is_file():
        benchmark = _read_required_text(benchmark_config)
        benchmark = _replace_once(
            benchmark,
            r'(?m)^(\s*internal const val TARGET_PACKAGE_NAME\s*=\s*")'
            r'((?:\\.|[^"\\])*)("\s*)$',
            lambda match: (
                f"{match.group(1)}{_kotlin_string(identity.application_id or '')}"
                f"{match.group(3)}"
            ),
            "benchmark target package",
        )
        benchmark_config.write_text(benchmark, encoding="utf-8")

    if project.posts_backend_url is not None:
        posts_network_path = _posts_network_module(root, config.identity.package_name)
        posts_network = _read_required_text(posts_network_path)
        posts_network = _replace_once(
            posts_network,
            r'(?m)^(\s*private const val POSTS_BASE_URL\s*=\s*")'
            r'((?:\\.|[^"\\])*)("\s*)$',
            lambda match: (
                f"{match.group(1)}{_kotlin_string(project.posts_backend_url or '')}"
                f"{match.group(3)}"
            ),
            "Posts example backend URL",
        )
        posts_network_path.write_text(posts_network, encoding="utf-8")


def _posts_network_module(root: Path, package_name: str) -> Path:
    return (
        root
        / "feature"
        / "posts"
        / "data"
        / "src"
        / "main"
        / "kotlin"
        / Path(*package_name.split("."))
        / "feature"
        / "posts"
        / "data"
        / "di"
        / "PostsNetworkModule.kt"
    )


def _benchmark_config(root: Path, package_name: str) -> Path:
    return (
        root
        / "benchmarks"
        / "src"
        / "main"
        / "java"
        / Path(*package_name.split("."))
        / "benchmarks"
        / "BenchmarkConfig.kt"
    )


def _read_required_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise SetupError(f"cannot read project setting source {path}: {error}") from error


def _required_match(text: str, pattern: str, label: str) -> str:
    match = re.search(pattern, text)
    if match is None:
        raise SetupError(f"cannot locate {label} in its project setting source")
    return match.group(1)


def _catalog_integer(catalog: str, key: str) -> int:
    return int(
        _required_match(
            catalog,
            rf'(?m)^{re.escape(key)}\s*=\s*"(\d+)"',
            key,
        ),
    )


def _replace_once(
    text: str,
    pattern: str,
    replacement: str | Callable[[Match[str]], str],
    label: str,
) -> str:
    updated, count = re.subn(pattern, replacement, text)
    if count != 1:
        raise SetupError(f"expected exactly one {label} setting, found {count}")
    return updated


def _kotlin_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")


def _unescape_kotlin_string(value: str) -> str:
    return value.replace("\\$", "$").replace('\\"', '"').replace("\\\\", "\\")


def _configure_ai_free_project(root: Path) -> None:
    try:
        for relative_path in AI_TOOLING_PATHS:
            path = root / relative_path
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
        for agent_guide in root.rglob("AGENTS.md"):
            agent_guide.unlink(missing_ok=True)
    except OSError as error:
        raise SetupError(f"could not remove AI guidance: {error}") from error

    retained = [
        relative_path
        for relative_path in AI_TOOLING_PATHS
        if (root / relative_path).exists() or (root / relative_path).is_symlink()
    ]
    retained.extend(
        str(path.relative_to(root))
        for path in root.rglob("AGENTS.md")
    )
    if retained:
        raise SetupError(
            "AI-free setup retained guidance paths: " + ", ".join(retained),
        )

    catalog_path = root / "gradle" / "libs.versions.toml"
    catalog = catalog_path.read_text(encoding="utf-8")
    catalog = re.sub(r"(?m)^generativeai\s*=.*\n", "", catalog)
    catalog_path.write_text(catalog, encoding="utf-8")

    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = re.sub(
        r"(?ms)^## 🤖 AI-assisted development\n.*?(?=^## )",
        "",
        readme,
    )
    readme = re.sub(
        r"(?m)^├── (?:\.agents/|AGENTS\.md|CLAUDE\.md).*\n",
        "",
        readme,
    )
    readme = re.sub(
        r"(?ms)^Enable the repository-owned pre-commit hook once per clone:\n\n"
        r"```bash\n.*?```\n\n"
        r"The hook checks staged Git blobs without reading ignored local credentials\. ",
        "",
        readme,
    )
    readme_path.write_text(readme, encoding="utf-8")

    architecture_path = root / "ARCHITECTURE.md"
    architecture = architecture_path.read_text(encoding="utf-8")
    architecture = architecture.replace(
        "Run the narrow module tests first, then use the validation matrix in\n"
        "[`.agents/reference/commands.md`](.agents/reference/commands.md).",
        "Run the narrow module tests first, then use `make verify` for the "
        "complete host-side validation contract.",
    )
    architecture_path.write_text(architecture, encoding="utf-8")

    gitignore_path = root / ".gitignore"
    gitignore = gitignore_path.read_text(encoding="utf-8")
    gitignore = re.sub(
        r"(?ms)^# Shared agent guidance is intentionally versioned\.\n"
        r"!AGENTS\.md\n"
        r"!CLAUDE\.md\n"
        r"!\.agents/\n"
        r"!\.agents/\*\*\n?",
        "",
        gitignore,
    )
    gitignore_path.write_text(gitignore, encoding="utf-8")

    pull_request_template = root / ".github" / "PULL_REQUEST_TEMPLATE"
    if pull_request_template.is_file():
        template = pull_request_template.read_text(encoding="utf-8")
        template = template.replace(
            "Documentation or agent guidance:",
            "Documentation:",
        )
        template = template.replace(
            "documentation, and agent-guidance impacts",
            "and documentation impacts",
        )
        pull_request_template.write_text(template, encoding="utf-8")

    _configure_ai_free_docs_check(root / "scripts" / "check-docs.sh")


def _configure_ai_free_docs_check(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for function_name in (
        "check_canonical_agent_entrypoint",
        "check_documented_modules",
        "check_pull_request_maintenance_contract",
    ):
        text = re.sub(
            rf"(?ms)^{function_name}\(\) \{{\n.*?^\}}\n\n?",
            "",
            text,
        )
        text = re.sub(
            rf"(?m)^{function_name}\n",
            "",
            text,
        )
    text = text.replace(
        "            README.md AGENTS.md .agents \\\n",
        "            README.md \\\n",
    )
    text = text.replace(
        'README.md AGENTS.md .agents)"; then',
        'README.md)"; then',
    )
    text = text.replace(
        "    for documentation_file in AGENTS.md README.md "
        ".agents/reference/commands.md; do",
        "    for documentation_file in README.md; do",
    )
    path.write_text(text, encoding="utf-8")


def _run_rename(root: Path, config: SetupConfig) -> None:
    identity = config.identity
    command = [
        sys.executable,
        str(root / "scripts" / "rename-template.py"),
        "--package",
        identity.package_name,
        "--name",
        identity.project_name,
        "--plugin-alias",
        identity.plugin_alias or derived_plugin_alias(identity.package_name),
        "--force",
    ]
    if identity.author:
        command.extend(("--author", identity.author))
    result = subprocess.run(
        command,
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SetupError(f"identity rename failed: {detail}")


def _validate_plugin_alias_collision(root: Path, config: SetupConfig) -> None:
    identity = json.loads(
        (root / "scripts" / "template-identity.json").read_text(encoding="utf-8"),
    )
    current_alias = identity["pluginAlias"]
    new_alias = (
        config.identity.plugin_alias
        or derived_plugin_alias(config.identity.package_name)
    )
    if current_alias == new_alias:
        return

    catalog = (root / "gradle" / "libs.versions.toml").read_text(encoding="utf-8")
    in_plugins = False
    aliases: set[str] = set()
    for line in catalog.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_plugins = stripped == "[plugins]"
            continue
        if not in_plugins or not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", maxsplit=1)[0].strip()
        top_level = re.split(r"[-_.]", key, maxsplit=1)[0]
        if top_level != current_alias:
            aliases.add(top_level)
    if new_alias in aliases:
        raise SetupError(
            f"plugin alias '{new_alias}' collides with an existing catalog accessor",
        )


def _configure_modules_and_dependencies(root: Path, config: SetupConfig) -> None:
    capabilities = config.capabilities
    settings_path = root / "settings.gradle.kts"
    settings = settings_path.read_text(encoding="utf-8")

    if config.starter.remove_examples:
        for relative_path in EXAMPLE_MODULES:
            shutil.rmtree(root / relative_path, ignore_errors=True)
        settings = _remove_settings_includes(settings, EXAMPLE_SETTINGS)

        if "navigation" not in capabilities:
            shutil.rmtree(root / "core" / "navigation", ignore_errors=True)
            settings = _remove_settings_includes(settings, (":core:navigation",))

    if "baseline_profiles" not in capabilities:
        shutil.rmtree(root / "benchmarks", ignore_errors=True)
        settings = _remove_settings_includes(settings, (":benchmarks",))

    settings_path.write_text(settings, encoding="utf-8")

    app_build_path = root / "app" / "build.gradle.kts"
    app_build = app_build_path.read_text(encoding="utf-8")
    if config.starter.remove_examples:
        # Derived from the removed includes so a new example module can never be
        # dropped from settings while a stale project(...) reference survives.
        app_build = _remove_project_dependencies(app_build, EXAMPLE_SETTINGS)

    if "hilt" not in capabilities:
        app_build = _replace_once(
            app_build,
            r'(?m)^(\s*testInstrumentationRunner\s*=\s*)"[^"]*"\s*$',
            lambda match: f'{match.group(1)}"androidx.test.runner.AndroidJUnitRunner"',
            "app instrumentation test runner",
        )

    app_build = _filter_capability_lines(app_build, capabilities)
    app_build = _remove_balanced_block(app_build, "dependencyGuard {")
    if "coverage" not in capabilities:
        app_build = _remove_balanced_block(app_build, 'getByName("sonar") {')
        app_build = _remove_balanced_block(
            app_build,
            'register<JacocoReport>("testCoverage") {',
        )
    app_build_path.write_text(app_build.rstrip() + "\n", encoding="utf-8")

    dependency_snapshot = root / "app" / "dependencies" / "releaseRuntimeClasspath.txt"
    dependency_snapshot.unlink(missing_ok=True)
    try:
        dependency_snapshot.parent.rmdir()
    except OSError:
        pass

    _configure_verification_contract(root, capabilities)
    if "visual_extras" not in capabilities:
        _install_system_typography(root, config.identity.package_name)


def _remove_project_dependencies(text: str, modules: Iterable[str]) -> str:
    """Drop every dependency line that targets one of ``modules``.

    Configurations are not matched, so ``androidTestImplementation`` and
    ``testImplementation`` references are removed alongside ``implementation``.
    """
    removed = tuple(f'project("{module}")' for module in modules)
    return "\n".join(
        line
        for line in text.splitlines()
        if not any(reference in line for reference in removed)
    ) + "\n"


def _filter_capability_lines(text: str, capabilities: frozenset[str]) -> str:
    result: list[str] = []
    for line in text.splitlines():
        required = None
        for token, capability_id in APP_PLUGIN_CAPABILITIES.items():
            if token in line:
                required = capability_id
                break
        if required is None:
            for token, capability_id in APP_DEPENDENCY_CAPABILITIES.items():
                if token in line:
                    required = capability_id
                    break

        enabled = True
        if required == "room_and_paging":
            enabled = "room" in capabilities and "paging" in capabilities
        elif required is not None:
            enabled = required in capabilities
        elif line.strip() == "jacoco":
            enabled = "coverage" in capabilities
        if enabled:
            result.append(line)
    return "\n".join(result) + "\n"


def _configure_verification_contract(
    root: Path,
    capabilities: frozenset[str],
) -> None:
    if "screenshots" in capabilities:
        return

    makefile_path = root / "Makefile"
    makefile = makefile_path.read_text(encoding="utf-8")
    for task in SCREENSHOT_VERIFICATION_TASKS:
        makefile = makefile.replace(f" {task}", "")
    makefile_path.write_text(makefile, encoding="utf-8")

    docs_check_path = root / "scripts" / "check-docs.sh"
    docs_check_path.write_text(
        _remove_required_verification_tasks(
            docs_check_path.read_text(encoding="utf-8"),
            SCREENSHOT_VERIFICATION_TASKS,
        ),
        encoding="utf-8",
    )


def _remove_required_verification_tasks(
    docs_check: str,
    tasks: Iterable[str],
) -> str:
    """Drop tasks from the ``check-docs.sh`` required verification task list.

    The list is matched structurally instead of as one literal block so that
    reordering or extending it in the template does not silently stop the
    wizard from relaxing the generated project's verification contract.
    """
    removed = frozenset(tasks)
    result: list[str] = []
    block: list[str] | None = None
    for line in docs_check.splitlines():
        if block is None:
            result.append(line)
            if line.strip() == "for required_task in \\":
                block = []
            continue
        block.append(line)
        if line.rstrip().endswith("; do"):
            result.extend(_rewrite_required_task_block(block, removed))
            block = None
    if block is not None:
        result.extend(block)
    return "\n".join(result) + "\n"


def _rewrite_required_task_block(
    block: list[str],
    removed: frozenset[str],
) -> list[str]:
    kept: list[tuple[str, str]] = []
    for line in block:
        task = line.strip().removesuffix("; do").removesuffix(" \\").strip()
        if task in removed:
            continue
        kept.append((line[: len(line) - len(line.lstrip())], task))

    if not kept:
        return block

    last_index = len(kept) - 1
    return [
        f"{indent}{task}; do" if index == last_index else f"{indent}{task} \\"
        for index, (indent, task) in enumerate(kept)
    ]


def _install_minimal_starter(root: Path, config: SetupConfig) -> None:
    package_path = Path(*config.identity.package_name.split("."))
    app_source = root / "app" / "src" / "main" / "kotlin" / package_path
    home_source = app_source / "home"
    shutil.rmtree(home_source / "navigation", ignore_errors=True)
    for filename in ("Greeting.kt", "MainScreens.kt"):
        (home_source / filename).unlink(missing_ok=True)

    android_test = root / "app" / "src" / "androidTest" / "kotlin" / package_path
    # HiltGraphTest injects the example posts repository, whose module is gone.
    for filename in ("MainNavigationTest.kt", "HiltGraphTest.kt"):
        (android_test / filename).unlink(missing_ok=True)
    if "hilt" not in config.capabilities:
        (android_test / "HiltTestRunner.kt").unlink(missing_ok=True)
    _prune_empty_directories(android_test)

    home_source.mkdir(parents=True, exist_ok=True)
    license_header = _license_header(root)
    (home_source / "MainActivity.kt").write_text(
        _main_activity_source(
            config.identity.package_name,
            hilt="hilt" in config.capabilities,
            license_header=license_header,
        ),
        encoding="utf-8",
    )
    (home_source / "StarterScreen.kt").write_text(
        _starter_screen_source(
            config.identity.package_name,
            license_header=license_header,
        ),
        encoding="utf-8",
    )

    manifest_path = root / "app" / "src" / "main" / "AndroidManifest.xml"
    manifest = manifest_path.read_text(encoding="utf-8")
    if "hilt" not in config.capabilities:
        (app_source / "App.kt").unlink(missing_ok=True)
        manifest = re.sub(
            r'\n\s*android:name="[^"]+\.App"',
            "",
            manifest,
            count=1,
        )
    if not config.capabilities.intersection({"networking", "coil", "generative_ai"}):
        manifest = re.sub(
            r'\n\s*<uses-permission android:name="android\.permission\.INTERNET" />',
            "",
            manifest,
            count=1,
        )
    manifest_path.write_text(manifest, encoding="utf-8")

    values_path = root / "app" / "src" / "main" / "res" / "values" / "strings.xml"
    values = values_path.read_text(encoding="utf-8")
    values = re.sub(r"\n\s*<string name=\"navigation_next\">.*?</string>", "", values)
    if 'name="starter_subtitle"' not in values:
        values = values.replace(
            "</resources>",
            "    <string name=\"starter_subtitle\">"
            "Your project is ready. Build something remarkable."
            "</string>\n</resources>",
        )
    values_path.write_text(values, encoding="utf-8")

    localized_path = (
        root / "app" / "src" / "main" / "res" / "values-pt-rPT" / "strings.xml"
    )
    if localized_path.is_file():
        localized = localized_path.read_text(encoding="utf-8")
        localized = re.sub(
            r"\n\s*<string name=\"navigation_next\">.*?</string>",
            "",
            localized,
        )
        if 'name="starter_subtitle"' not in localized:
            localized = localized.replace(
                "</resources>",
                "    <string name=\"starter_subtitle\">"
                "O seu projeto está pronto. Crie algo extraordinário."
                "</string>\n</resources>",
            )
        localized_path.write_text(localized, encoding="utf-8")


def _install_system_typography(root: Path, package_name: str) -> None:
    package_path = Path(*package_name.split("."))
    typography_path = (
        root
        / "app"
        / "src"
        / "main"
        / "kotlin"
        / package_path
        / "ui"
        / "theme"
        / "Typography.kt"
    )
    if not typography_path.is_file():
        return
    license_header = _license_header(root)
    typography_path.write_text(
        f"""{license_header}

package {package_name}.ui.theme

import androidx.compose.ui.text.font.FontFamily

val LexendDecaFontFamily: FontFamily = FontFamily.SansSerif
""",
        encoding="utf-8",
    )


def _license_header(root: Path) -> str:
    header_path = root / "spotless" / "copyright.kt"
    try:
        header = header_path.read_text(encoding="utf-8").rstrip()
    except OSError as error:
        raise SetupError(f"cannot read Kotlin license header: {error}") from error
    return header.replace("$YEAR", str(date.today().year))


def _main_activity_source(
    package_name: str,
    *,
    hilt: bool,
    license_header: str,
) -> str:
    hilt_import = (
        "import dagger.hilt.android.AndroidEntryPoint\n"
        if hilt
        else ""
    )
    hilt_annotation = "@AndroidEntryPoint\n" if hilt else ""
    return f"""{license_header}

package {package_name}.home

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.core.view.WindowCompat
import {package_name}.ui.setEdgeToEdgeConfig
import {package_name}.ui.theme.TemplateTheme
{hilt_import}
{hilt_annotation}class MainActivity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        setEdgeToEdgeConfig()
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)

        setContent {{
            TemplateTheme {{
                StarterScreen(modifier = Modifier.fillMaxSize())
            }}
        }}
    }}
}}
"""


def _starter_screen_source(package_name: str, *, license_header: str) -> str:
    application_package = _application_package_from_identity(package_name)
    return f"""{license_header}

package {package_name}.home

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import {package_name}.ui.theme.TemplateTheme
import {application_package}.R

@Composable
fun StarterScreen(
    modifier: Modifier = Modifier,
) {{
    Box(
        contentAlignment = Alignment.Center,
        modifier = modifier
            .background(MaterialTheme.colorScheme.surfaceContainer)
            .safeDrawingPadding()
            .padding(24.dp),
    ) {{
        Surface(
            tonalElevation = 6.dp,
            shadowElevation = 12.dp,
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(32.dp)),
            shape = RoundedCornerShape(32.dp),
        ) {{
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(16.dp),
                modifier = Modifier.padding(horizontal = 32.dp, vertical = 48.dp),
            ) {{
                Text(
                    text = stringResource(R.string.app_name),
                    textAlign = TextAlign.Center,
                    fontWeight = FontWeight.Bold,
                    style = MaterialTheme.typography.headlineLarge,
                )
                Text(
                    text = stringResource(R.string.starter_subtitle),
                    textAlign = TextAlign.Center,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyLarge,
                )
            }}
        }}
    }}
}}

@Preview
@Composable
private fun StarterScreenPreview() {{
    TemplateTheme {{
        StarterScreen()
    }}
}}
"""


def _application_package_from_identity(code_package: str) -> str:
    identity_path = default_source_root() / "scripts" / "template-identity.json"
    try:
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return code_package
    current_code = identity.get("codePackage")
    current_application = identity.get("applicationPackage")
    if code_package == current_code and isinstance(current_application, str):
        return current_application
    return code_package


def _remove_settings_includes(text: str, module_paths: Iterable[str]) -> str:
    module_set = set(module_paths)
    return "\n".join(
        line
        for line in text.splitlines()
        if not any(f'include("{module}")' in line for module in module_set)
    ) + "\n"


def _remove_balanced_block(text: str, marker: str) -> str:
    start = text.find(marker)
    if start < 0:
        return text
    line_start = text.rfind("\n", 0, start) + 1
    brace_start = text.find("{", start)
    if brace_start < 0:
        return text
    depth = 0
    for index in range(brace_start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                while end < len(text) and text[end] in " \t":
                    end += 1
                if end < len(text) and text[end] == "\n":
                    end += 1
                return text[:line_start] + text[end:]
    raise SetupError(f"could not parse build block beginning with {marker}")


def _neutralize_missing_markdown_links(root: Path) -> None:
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    for markdown_path in root.rglob("*.md"):
        if any(part in SKIPPED_DIRECTORIES for part in markdown_path.parts):
            continue
        text = markdown_path.read_text(encoding="utf-8")
        relative_parent = markdown_path.parent

        def replace_link(match: re.Match[str]) -> str:
            label, raw_target = match.groups()
            target = raw_target.strip("<>")
            if (
                not target
                or target.startswith(("#", "http://", "https://", "mailto:", "tel:", "app://"))
            ):
                return match.group(0)
            target = target.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0]
            if target.startswith("/"):
                return match.group(0)
            if (relative_parent / target).exists():
                return match.group(0)
            return f"`{label}`"

        replacement = link_pattern.sub(replace_link, text)
        if replacement != text:
            markdown_path.write_text(replacement, encoding="utf-8")


def _sort_kotlin_imports(root: Path) -> None:
    import_block = re.compile(r"(?m)^(?:import [^\n]+\n)+")
    for kotlin_path in root.rglob("*.kt"):
        if any(part in SKIPPED_DIRECTORIES for part in kotlin_path.parts):
            continue
        text = kotlin_path.read_text(encoding="utf-8")

        def sort_block(match: re.Match[str]) -> str:
            lines = match.group(0).splitlines()
            return "\n".join(sorted(lines, key=_kotlin_import_sort_key)) + "\n"

        replacement = import_block.sub(sort_block, text, count=1)
        if replacement != text:
            kotlin_path.write_text(replacement, encoding="utf-8")


def _kotlin_import_sort_key(line: str) -> tuple[int, str]:
    imported = line[len("import ") :] if line.startswith("import ") else line
    if " as " in imported:
        group = 4
    elif imported.startswith("java."):
        group = 1
    elif imported.startswith("javax."):
        group = 2
    elif imported.startswith("kotlin."):
        group = 3
    else:
        group = 0
    return group, imported


def _run_selected_validation(root: Path, config: SetupConfig) -> None:
    commands: list[list[str]] = []
    if config.validation.format:
        commands.append(["./gradlew", "spotlessApply"])
    if config.validation.level == "narrow":
        commands.append(
            ["./gradlew", ":app:assembleDebug", ":app:testDebugUnitTest"],
        )
    elif config.validation.level == "full":
        commands.append(["make", "verify"])

    for command in commands:
        result = subprocess.run(command, cwd=root, check=False)
        if result.returncode != 0:
            raise SetupError(
                f"generated project validation failed: {' '.join(command)}",
            )


def _tracked_files(root: Path) -> list[Path]:
    if _is_git_root(root):
        try:
            result = subprocess.run(
                ("git", "ls-files", "-z", "--cached"),
                cwd=root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            result = None
        if result is not None and result.returncode == 0:
            return _existing_source_paths(root, result.stdout)
    return _manifest_files(root)


def _manifest_files(root: Path) -> list[Path]:
    manifest_path = root / SOURCE_MANIFEST_PATH
    try:
        lines = manifest_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise SetupError(
            "source repository has no Git inventory or setup-wizard source manifest",
        ) from error

    result: list[Path] = []
    seen: set[Path] = set()
    for line in lines:
        relative_path = Path(line)
        if (
            not line
            or "\\" in line
            or relative_path.is_absolute()
            or relative_path.as_posix() != line
            or any(part in {".", ".."} for part in relative_path.parts)
        ):
            raise SetupError(f"invalid source manifest entry: {line!r}")
        if relative_path in seen:
            raise SetupError(f"duplicate source manifest entry: {line}")
        if not _source_path_is_eligible(relative_path):
            raise SetupError(f"ineligible source manifest entry: {line}")
        path = root / relative_path
        if not path.is_file() and not path.is_symlink():
            raise SetupError(f"source manifest entry is missing: {line}")
        seen.add(relative_path)
        result.append(relative_path)

    if SOURCE_MANIFEST_PATH not in seen:
        raise SetupError(
            f"source manifest must include {SOURCE_MANIFEST_PATH.as_posix()}",
        )
    return sorted(result)


def _write_source_manifest(root: Path, paths: Iterable[Path]) -> None:
    entries = {
        Path(path)
        for path in paths
        if _source_path_is_eligible(Path(path))
    }
    entries.add(SOURCE_MANIFEST_PATH)
    manifest_path = root / SOURCE_MANIFEST_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "".join(f"{path.as_posix()}\n" for path in sorted(entries)),
        encoding="utf-8",
    )


def _repository_files(root: Path) -> list[Path]:
    if not _is_git_root(root):
        return _walk_files(root)
    result = subprocess.run(
        (
            "git",
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ),
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return _existing_source_paths(root, result.stdout)
    return _walk_files(root)


def _existing_source_paths(root: Path, raw_paths: bytes) -> list[Path]:
    result: list[Path] = []
    for raw_path in raw_paths.split(b"\0"):
        if not raw_path:
            continue
        relative_path = Path(os.fsdecode(raw_path))
        path = root / relative_path
        if _source_path_is_eligible(relative_path) and (
            path.is_file() or path.is_symlink()
        ):
            result.append(relative_path)
    return sorted(result)


def _walk_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for directory, child_directories, filenames in os.walk(root):
        child_directories[:] = sorted(
            name for name in child_directories if name not in SKIPPED_DIRECTORIES
        )
        directory_path = Path(directory)
        result.extend(
            relative_path
            for filename in sorted(filenames)
            for relative_path in (
                (directory_path / filename).relative_to(root),
            )
            if _source_path_is_eligible(relative_path)
        )
    return result


def _source_path_is_eligible(relative_path: Path) -> bool:
    return (
        not relative_path.is_absolute()
        and not any(part in SKIPPED_DIRECTORIES for part in relative_path.parts)
        and relative_path.name not in SKIPPED_LOCAL_FILES
        and not relative_path.name.startswith(".env")
        and not relative_path.name.endswith((".pyc", ".pyo"))
    )


def _git_is_dirty(root: Path) -> bool:
    if not _is_git_root(root):
        return False
    result = subprocess.run(
        ("git", "status", "--porcelain", "--untracked-files=all"),
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def _is_git_root(root: Path) -> bool:
    try:
        result = subprocess.run(
            ("git", "rev-parse", "--show-toplevel"),
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        return False
    if result.returncode != 0:
        return False
    try:
        return Path(result.stdout.strip()).resolve() == root.resolve()
    except OSError:
        return False


def _source_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    files = _repository_files(root) if _is_git_root(root) else _tracked_files(root)
    for relative_path in files:
        path = root / relative_path
        digest.update(os.fsencode(relative_path))
        if path.is_symlink():
            digest.update(os.fsencode(os.readlink(path)))
        else:
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _prune_empty_directories(root: Path) -> None:
    directories = sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        if any(part in SKIPPED_DIRECTORIES for part in directory.parts):
            continue
        try:
            directory.rmdir()
        except OSError:
            pass


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
