"""Planning and transactional application for project setup."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import (
    CAPABILITY_BY_ID,
    SetupConfig,
    derived_plugin_alias,
    validate_config,
    with_resolved_capabilities,
)


SKIPPED_DIRECTORIES = {".git", ".gradle", ".idea", ".kotlin", "build"}
SKIPPED_LOCAL_FILES = {"local.properties", "key.properties"}
EXAMPLE_MODULES = (
    "feature/home",
    "feature/posts",
    "feature/database",
    "library-android",
    "library-kotlin",
)
EXAMPLE_SETTINGS = (
    ':feature:database',
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
    target_root: Path
    config: SetupConfig
    reasons: dict[str, str]
    operations: tuple[str, ...]
    digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "digest": self.digest,
            "sourceRoot": str(self.source_root),
            "targetRoot": str(self.target_root),
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
    else:
        target = source

    identity_bytes = identity_path.read_bytes()
    operations = [
        (
            f"Copy tracked template files to {target}"
            if resolved_config.output.mode == "copy"
            else f"Configure the current repository at {source}"
        ),
        (
            f"Rename project to “{resolved_config.identity.project_name}” "
            f"with package {resolved_config.identity.package_name}"
        ),
        f"Enable {len(resolved_config.capabilities)} optional capability group(s)",
    ]
    if resolved_config.starter.remove_examples:
        operations.append(
            "Remove example features and sample libraries; generate a minimal Compose starter",
        )
        if "navigation" not in resolved_config.capabilities:
            operations.append("Remove the unused core navigation module")
        if "baseline_profiles" not in resolved_config.capabilities:
            operations.append("Remove the benchmark module and baseline-profile wiring")
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
    else:
        result = _apply_in_place(plan, force=force)

    _run_selected_validation(result, plan.config)
    return result


def _apply_to_copy(plan: SetupPlan) -> Path:
    destination = plan.target_root
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
        for relative_path in _tracked_files(plan.source_root):
            source = plan.source_root / relative_path
            target = staging / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                target.symlink_to(os.readlink(source))
            else:
                shutil.copy2(source, target)
        _configure_repository(staging, plan.config)
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
    _configure_modules_and_dependencies(root, config)
    if config.starter.remove_examples:
        _install_minimal_starter(root, config)
    _sort_kotlin_imports(root)
    _neutralize_missing_markdown_links(root)


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
        app_build = "\n".join(
            line
            for line in app_build.splitlines()
            if not any(
                f'project("{module}")' in line
                for module in (
                    ":feature:home",
                    ":feature:posts:data",
                    ":feature:posts:presentation",
                )
            )
        ) + "\n"

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
    if "screenshots" not in capabilities:
        makefile_path = root / "Makefile"
        makefile = makefile_path.read_text(encoding="utf-8")
        makefile = makefile.replace(" validateDebugScreenshotTest", "")
        makefile = makefile.replace(" verifyRoborazziDebug", "")
        makefile_path.write_text(makefile, encoding="utf-8")

        docs_check_path = root / "scripts" / "check-docs.sh"
        docs_check = docs_check_path.read_text(encoding="utf-8")
        docs_check = docs_check.replace(
            "        localization-check \\\n"
            "        validateDebugScreenshotTest \\\n"
            "        verifyRoborazziDebug; do",
            "        localization-check; do",
        )
        docs_check_path.write_text(docs_check, encoding="utf-8")


def _install_minimal_starter(root: Path, config: SetupConfig) -> None:
    package_path = Path(*config.identity.package_name.split("."))
    app_source = root / "app" / "src" / "main" / "kotlin" / package_path
    home_source = app_source / "home"
    shutil.rmtree(home_source / "navigation", ignore_errors=True)
    for filename in ("Greeting.kt", "MainScreens.kt"):
        (home_source / filename).unlink(missing_ok=True)

    android_test = root / "app" / "src" / "androidTest" / "kotlin" / package_path
    (android_test / "MainNavigationTest.kt").unlink(missing_ok=True)
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
    if not _is_git_root(root):
        return _walk_files(root)
    result = subprocess.run(
        ("git", "ls-files", "-z", "--cached"),
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        return sorted(
            Path(os.fsdecode(value))
            for value in result.stdout.split(b"\0")
            if value and (root / os.fsdecode(value)).is_file()
        )
    return _walk_files(root)


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
        return sorted(
            Path(os.fsdecode(value))
            for value in result.stdout.split(b"\0")
            if value and (root / os.fsdecode(value)).is_file()
        )
    return _walk_files(root)


def _walk_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for directory, child_directories, filenames in os.walk(root):
        child_directories[:] = sorted(
            name for name in child_directories if name not in SKIPPED_DIRECTORIES
        )
        directory_path = Path(directory)
        result.extend(
            (directory_path / filename).relative_to(root)
            for filename in sorted(filenames)
            if filename not in SKIPPED_LOCAL_FILES and not filename.startswith(".env")
        )
    return result


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
    result = subprocess.run(
        ("git", "rev-parse", "--show-toplevel"),
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if result.returncode != 0:
        return False
    try:
        return Path(result.stdout.strip()).resolve() == root.resolve()
    except OSError:
        return False


def _source_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for relative_path in _repository_files(root):
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
