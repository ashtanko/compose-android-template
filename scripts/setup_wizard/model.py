"""Configuration schema and capability resolution for the setup wizard."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


SCHEMA_VERSION = 3
SUPPORTED_SCHEMA_VERSIONS = frozenset({1, 2, SCHEMA_VERSION})
PACKAGE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
PLUGIN_ALIAS_PATTERN = re.compile(r"^[a-z][a-z0-9]*$")
RESERVED_WORDS = {
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
    "private",
    "protected",
    "public",
    "reified",
    "return",
    "sealed",
    "set",
    "short",
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


@dataclass(frozen=True)
class Capability:
    id: str
    title: str
    description: str
    category: str
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectSettingDefinition:
    key: str
    title: str
    description: str
    category: str
    input_type: str
    source: str
    editable: bool = True
    minimum: int | None = None
    maximum: int | None = None
    section: str = "projectSettings"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.key,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "inputType": self.input_type,
            "source": self.source,
            "editable": self.editable,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "section": self.section,
        }


@dataclass(frozen=True)
class ConfigurationSurface:
    id: str
    title: str
    description: str
    disposition: str
    sources: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "disposition": self.disposition,
            "sources": list(self.sources),
        }


CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        "navigation",
        "Navigation 3",
        "Type-safe Compose navigation and the shared navigation module.",
        "Architecture",
        ("serialization",),
    ),
    Capability(
        "coroutines",
        "Kotlin Coroutines",
        "Structured asynchronous work and coroutine test support.",
        "Architecture",
    ),
    Capability(
        "serialization",
        "Kotlin Serialization",
        "JSON and serializable route/model support.",
        "Architecture",
    ),
    Capability(
        "hilt",
        "Hilt",
        "Dependency injection with the repository convention plugin.",
        "Architecture",
    ),
    Capability(
        "networking",
        "Networking",
        "Retrofit, OkHttp, and the Kotlin serialization converter.",
        "Data",
        ("coroutines", "serialization"),
    ),
    Capability(
        "room",
        "Room",
        "Local persistence through Room and KSP.",
        "Data",
        ("coroutines",),
    ),
    Capability(
        "paging",
        "Paging",
        "Paging runtime and Compose integration.",
        "Data",
        ("coroutines",),
    ),
    Capability(
        "coil",
        "Coil",
        "Compose image loading, including SVG support.",
        "UI",
        ("coroutines",),
    ),
    Capability(
        "adaptive_ui",
        "Adaptive UI",
        "Material adaptive layouts, window information, and navigation suites.",
        "UI",
    ),
    Capability(
        "permissions",
        "Permissions",
        "Accompanist permission helpers for runtime permission flows.",
        "Platform",
    ),
    Capability(
        "visual_extras",
        "Fonts and icons",
        "Google Fonts and the extended Material icon set.",
        "UI",
    ),
    Capability(
        "generative_ai",
        "Generative AI",
        "The Google generative AI Android client.",
        "Platform",
        ("coroutines",),
    ),
    Capability(
        "test_tooling",
        "Extended test tooling",
        "Turbine, Mockito, MockK, Robolectric, Espresso, and architecture tests.",
        "Tooling",
        ("coroutines",),
    ),
    Capability(
        "screenshots",
        "Screenshot testing",
        "Compose screenshot and Roborazzi verification.",
        "Tooling",
    ),
    Capability(
        "coverage",
        "Coverage",
        "JaCoCo, Kover, and Sonar coverage integration.",
        "Tooling",
    ),
    Capability(
        "baseline_profiles",
        "Baseline profiles",
        "Macrobenchmark and baseline profile generation.",
        "Tooling",
    ),
)

CAPABILITY_BY_ID = {capability.id: capability for capability in CAPABILITIES}

PROJECT_SETTING_DEFINITIONS: tuple[ProjectSettingDefinition, ...] = (
    ProjectSettingDefinition(
        "applicationId",
        "Application ID",
        "Install and Play identity. Defaults to the code package when left unset.",
        "App identity",
        "text",
        "app/build.gradle.kts",
        section="identity",
    ),
    ProjectSettingDefinition(
        "displayName",
        "App display name",
        "Launcher label. Defaults to the Gradle project name when left unset.",
        "App identity",
        "text",
        "app/src/main/res/values/strings.xml",
        section="identity",
    ),
    ProjectSettingDefinition(
        "versionCode",
        "Version code",
        "Positive integer used by Android and app stores for upgrade ordering.",
        "App version",
        "number",
        "app/build.gradle.kts",
        True,
        1,
        2_100_000_000,
    ),
    ProjectSettingDefinition(
        "versionName",
        "Version name",
        "User-visible release version such as 1.0.0.",
        "App version",
        "text",
        "app/build.gradle.kts",
    ),
    ProjectSettingDefinition(
        "compileSdk",
        "Compile SDK",
        "Android API level used to compile every Android module.",
        "Android toolchain",
        "number",
        "gradle/libs.versions.toml",
        True,
        35,
        99,
    ),
    ProjectSettingDefinition(
        "minSdk",
        "Minimum SDK",
        "Oldest Android API level supported by the application.",
        "Android toolchain",
        "number",
        "gradle/libs.versions.toml",
        True,
        21,
        99,
    ),
    ProjectSettingDefinition(
        "targetSdk",
        "Target SDK",
        "Android behavior level the application opts into.",
        "Android toolchain",
        "number",
        "gradle/libs.versions.toml",
        True,
        21,
        99,
    ),
    ProjectSettingDefinition(
        "benchmarkMinSdk",
        "Benchmark minimum SDK",
        "Oldest API level allowed for the macrobenchmark module.",
        "Android toolchain",
        "number",
        "gradle/libs.versions.toml",
        True,
        23,
        99,
    ),
    ProjectSettingDefinition(
        "jvmTarget",
        "JVM bytecode target",
        "Java and Kotlin bytecode level; the build itself still requires JDK 21.",
        "Android toolchain",
        "number",
        "gradle/libs.versions.toml",
        False,
        17,
        25,
    ),
    ProjectSettingDefinition(
        "postsBackendUrl",
        "Posts example backend URL",
        "Retrofit base URL used only when the example modules are retained.",
        "Example configuration",
        "url",
        "feature/posts/data/.../PostsNetworkModule.kt",
    ),
)

CONFIGURATION_SURFACES: tuple[ConfigurationSurface, ...] = (
    ConfigurationSurface(
        "identity",
        "Project and package identity",
        "Project name, code package, application ID, plugin alias, and optional author.",
        "editable",
        ("scripts/template-identity.json", "settings.gradle.kts", "app/build.gradle.kts"),
    ),
    ConfigurationSurface(
        "app-metadata",
        "App metadata and SDK levels",
        "Display name, release version, Android SDK levels, and the retained-example backend.",
        "editable",
        ("app/build.gradle.kts", "gradle/libs.versions.toml", "feature/posts/data"),
    ),
    ConfigurationSurface(
        "modules",
        "Module topology",
        "Starter selection and capability rules retain or remove the example and benchmark modules.",
        "derived",
        ("settings.gradle.kts", "scripts/add-module.sh"),
    ),
    ConfigurationSurface(
        "dependencies",
        "Dependencies and plugins",
        "Curated capabilities control active app dependencies; versions remain catalog-managed.",
        "derived",
        ("gradle/libs.versions.toml", "build.gradle.kts", "app/build.gradle.kts"),
    ),
    ConfigurationSurface(
        "build-runtime",
        "Gradle execution and performance",
        "Memory, parallelism, build cache, configuration cache, and AndroidX flags are inherited.",
        "inherited",
        ("gradle.properties", "gradle/gradle-daemon-jvm.properties"),
    ),
    ConfigurationSurface(
        "build-types",
        "Build types, shrinking, and packaging",
        "Debug, release, benchmark, R8, and packaging policies stay on repository defaults.",
        "inherited",
        ("app/build.gradle.kts", "app/proguard-rules.pro", "app/benchmark-rules.pro"),
    ),
    ConfigurationSurface(
        "branding",
        "Brand assets and localization",
        "The label is editable; launcher artwork, theme tokens, locales, and translations are manual follow-up work.",
        "manual",
        ("app/src/main/res", "LOCALIZATION.md"),
    ),
    ConfigurationSurface(
        "client-secrets",
        "Client configuration defaults",
        "The inactive secrets.defaults.properties fallback is inherited; client values are never treated as secrets.",
        "inherited",
        ("secrets.defaults.properties", "build.gradle.kts"),
    ),
    ConfigurationSurface(
        "signing",
        "Signing and CI credentials",
        "Secrets are never collected. Generated projects retain the key.properties and SIGNING_* environment contract.",
        "manual",
        ("key.properties.example", "RELEASING.md", ".github/workflows"),
    ),
    ConfigurationSurface(
        "quality",
        "Formatting, verification, and agent guidance",
        "Output mode controls safe checks; AI-free mode can remove coding-agent guidance.",
        "editable",
        ("Makefile", ".agents", "scripts/check-template-tools.sh"),
    ),
)

PRESETS: dict[str, frozenset[str]] = {
    "minimal": frozenset(),
    "standard": frozenset(
        {
            "navigation",
            "coroutines",
            "serialization",
            "hilt",
            "networking",
            "room",
            "coil",
            "adaptive_ui",
            "test_tooling",
        },
    ),
    "full": frozenset(capability.id for capability in CAPABILITIES),
}

EXAMPLE_REQUIREMENTS = frozenset(
    {
        "navigation",
        "coroutines",
        "serialization",
        "hilt",
        "networking",
        "adaptive_ui",
        "test_tooling",
        "screenshots",
    },
)


@dataclass(frozen=True)
class IdentityConfig:
    package_name: str
    project_name: str
    application_id: str | None = None
    display_name: str | None = None
    plugin_alias: str | None = None
    author: str | None = None


@dataclass(frozen=True)
class OutputConfig:
    mode: str = "copy"
    path: str | None = None


@dataclass(frozen=True)
class StarterConfig:
    remove_examples: bool = True
    ai_free: bool = False


@dataclass(frozen=True)
class ValidationConfig:
    format: bool = False
    level: str = "none"


@dataclass(frozen=True)
class ProjectSettingsConfig:
    version_code: int | None = None
    version_name: str | None = None
    compile_sdk: int | None = None
    min_sdk: int | None = None
    target_sdk: int | None = None
    benchmark_min_sdk: int | None = None
    jvm_target: int | None = None
    posts_backend_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "versionCode": self.version_code,
            "versionName": self.version_name,
            "compileSdk": self.compile_sdk,
            "minSdk": self.min_sdk,
            "targetSdk": self.target_sdk,
            "benchmarkMinSdk": self.benchmark_min_sdk,
            "jvmTarget": self.jvm_target,
            "postsBackendUrl": self.posts_backend_url,
        }


@dataclass(frozen=True)
class SetupConfig:
    identity: IdentityConfig
    output: OutputConfig = field(default_factory=OutputConfig)
    starter: StarterConfig = field(default_factory=StarterConfig)
    project_settings: ProjectSettingsConfig = field(
        default_factory=ProjectSettingsConfig,
    )
    capabilities: frozenset[str] = field(default_factory=frozenset)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SetupConfig":
        if not isinstance(value, dict):
            raise ValueError("configuration must be a JSON object")
        schema_version = value.get("schemaVersion", SCHEMA_VERSION)
        if (
            isinstance(schema_version, bool)
            or not isinstance(schema_version, int)
            or schema_version not in SUPPORTED_SCHEMA_VERSIONS
        ):
            raise ValueError(
                f"unsupported schemaVersion {schema_version}; "
                f"expected one of {sorted(SUPPORTED_SCHEMA_VERSIONS)}",
            )

        identity_value = _object(value, "identity")
        output_value = _object(value, "output", required=False)
        starter_value = _object(value, "starter", required=False)
        project_settings_value = _object(
            value,
            "projectSettings",
            required=False,
        )
        validation_value = _object(value, "validation", required=False)
        if schema_version == SCHEMA_VERSION:
            _reject_unknown_keys(
                value,
                {
                    "schemaVersion",
                    "identity",
                    "output",
                    "starter",
                    "projectSettings",
                    "capabilities",
                    "validation",
                },
                "configuration",
            )
            _reject_unknown_keys(
                identity_value,
                {
                    "packageName",
                    "projectName",
                    "applicationId",
                    "displayName",
                    "pluginAlias",
                    "author",
                },
                "identity",
            )
            _reject_unknown_keys(output_value, {"mode", "path"}, "output")
            _reject_unknown_keys(
                starter_value,
                {"removeExamples", "aiFree"},
                "starter",
            )
            _reject_unknown_keys(
                project_settings_value,
                {
                    "versionCode",
                    "versionName",
                    "compileSdk",
                    "minSdk",
                    "targetSdk",
                    "benchmarkMinSdk",
                    "jvmTarget",
                    "postsBackendUrl",
                },
                "projectSettings",
            )
            _reject_unknown_keys(
                validation_value,
                {"format", "level"},
                "validation",
            )
        raw_capabilities = value.get("capabilities", [])
        if not isinstance(raw_capabilities, list) or not all(
            isinstance(item, str) for item in raw_capabilities
        ):
            raise ValueError("capabilities must be an array of capability IDs")

        package_name = _string(identity_value, "packageName")
        project_name = _string(identity_value, "projectName")
        application_id = _optional_string(identity_value, "applicationId")
        display_name = _optional_string(identity_value, "displayName")
        if schema_version < SCHEMA_VERSION:
            application_id = application_id or package_name
            display_name = display_name or project_name

        config = cls(
            identity=IdentityConfig(
                package_name=package_name,
                project_name=project_name,
                application_id=application_id,
                display_name=display_name,
                plugin_alias=_optional_string(identity_value, "pluginAlias"),
                author=_optional_string(identity_value, "author"),
            ),
            output=OutputConfig(
                mode=_string(output_value, "mode", default="copy"),
                path=_optional_string(output_value, "path"),
            ),
            starter=StarterConfig(
                remove_examples=_boolean(
                    starter_value,
                    "removeExamples",
                    default=True,
                ),
                ai_free=_boolean(
                    starter_value,
                    "aiFree",
                    default=False,
                ),
            ),
            project_settings=ProjectSettingsConfig(
                version_code=_optional_integer(
                    project_settings_value,
                    "versionCode",
                ),
                version_name=_optional_string(
                    project_settings_value,
                    "versionName",
                ),
                compile_sdk=_optional_integer(
                    project_settings_value,
                    "compileSdk",
                ),
                min_sdk=_optional_integer(project_settings_value, "minSdk"),
                target_sdk=_optional_integer(
                    project_settings_value,
                    "targetSdk",
                ),
                benchmark_min_sdk=_optional_integer(
                    project_settings_value,
                    "benchmarkMinSdk",
                ),
                jvm_target=_optional_integer(
                    project_settings_value,
                    "jvmTarget",
                ),
                posts_backend_url=_optional_string(
                    project_settings_value,
                    "postsBackendUrl",
                ),
            ),
            capabilities=frozenset(raw_capabilities),
            validation=ValidationConfig(
                format=_boolean(validation_value, "format", default=False),
                level=_string(validation_value, "level", default="none"),
            ),
            schema_version=SCHEMA_VERSION,
        )
        validate_config(config)
        return config

    @classmethod
    def from_json_file(cls, path: Path) -> "SetupConfig":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"cannot read configuration {path}: {error}") from error
        return cls.from_dict(value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "identity": {
                "packageName": self.identity.package_name,
                "projectName": self.identity.project_name,
                "applicationId": self.identity.application_id,
                "displayName": self.identity.display_name,
                "pluginAlias": self.identity.plugin_alias,
                "author": self.identity.author,
            },
            "output": {
                "mode": self.output.mode,
                "path": self.output.path,
            },
            "starter": {
                "removeExamples": self.starter.remove_examples,
                "aiFree": self.starter.ai_free,
            },
            "projectSettings": self.project_settings.to_dict(),
            "capabilities": sorted(self.capabilities),
            "validation": {
                "format": self.validation.format,
                "level": self.validation.level,
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def _object(
    value: dict[str, Any],
    key: str,
    *,
    required: bool = True,
) -> dict[str, Any]:
    result = value.get(key)
    if result is None and not required:
        return {}
    if not isinstance(result, dict):
        raise ValueError(f"{key} must be an object")
    return result


def _string(
    value: dict[str, Any],
    key: str,
    *,
    default: str | None = None,
) -> str:
    result = value.get(key, default)
    if not isinstance(result, str) or not result:
        raise ValueError(f"{key} must be a non-empty string")
    return result


def _optional_string(value: dict[str, Any], key: str) -> str | None:
    result = value.get(key)
    if result is None:
        return None
    if not isinstance(result, str):
        raise ValueError(f"{key} must be a string or null")
    return result or None


def _optional_integer(value: dict[str, Any], key: str) -> int | None:
    result = value.get(key)
    if result is None:
        return None
    if isinstance(result, bool) or not isinstance(result, int):
        raise ValueError(f"{key} must be an integer or null")
    return result


def _reject_unknown_keys(
    value: dict[str, Any],
    allowed: set[str],
    field_name: str,
) -> None:
    unknown = sorted(set(value).difference(allowed))
    if unknown:
        raise ValueError(
            f"{field_name} contains unknown fields: {', '.join(unknown)}",
        )


def _boolean(
    value: dict[str, Any],
    key: str,
    *,
    default: bool,
) -> bool:
    result = value.get(key, default)
    if not isinstance(result, bool):
        raise ValueError(f"{key} must be true or false")
    return result


def validate_single_line(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if "\n" in value or "\r" in value:
        raise ValueError(f"{field_name} must be a single line")
    for character in value:
        codepoint = ord(character)
        if not (
            codepoint in (0x09,)
            or 0x20 <= codepoint <= 0xD7FF
            or 0xE000 <= codepoint <= 0xFFFD
            or 0x10000 <= codepoint <= 0x10FFFF
        ):
            raise ValueError(
                f"{field_name} contains a character that XML 1.0 cannot represent",
            )


def derived_plugin_alias(package_name: str) -> str:
    return package_name.rsplit(".", maxsplit=1)[-1].replace("_", "")


def validate_config(config: SetupConfig) -> None:
    identity = config.identity
    _validate_package_identifier(identity.package_name, "packageName")
    if identity.application_id is not None:
        _validate_package_identifier(identity.application_id, "applicationId")
    if identity.display_name is not None:
        validate_single_line(identity.display_name, "displayName")

    validate_single_line(identity.project_name, "projectName")
    plugin_alias = identity.plugin_alias or derived_plugin_alias(identity.package_name)
    if not PLUGIN_ALIAS_PATTERN.fullmatch(plugin_alias):
        raise ValueError(
            "pluginAlias must start with a lowercase letter and contain only "
            "lowercase letters and digits",
        )
    if identity.author is not None:
        validate_single_line(identity.author, "author")
        if "*/" in identity.author or "--" in identity.author:
            raise ValueError("author contains an unsafe comment terminator")

    if config.output.mode not in {"archive", "copy", "inPlace"}:
        raise ValueError("output.mode must be 'archive', 'copy', or 'inPlace'")
    if config.output.mode == "copy" and not config.output.path:
        raise ValueError("output.path is required in copy mode")
    if config.output.mode != "copy" and config.output.path:
        raise ValueError("output.path must be omitted outside copy mode")
    if config.output.mode == "archive" and (
        config.validation.format or config.validation.level != "none"
    ):
        raise ValueError(
            "archive mode supports structural checks only",
        )
    if config.validation.level not in {"none", "narrow", "full"}:
        raise ValueError("validation.level must be none, narrow, or full")

    project = config.project_settings
    if project.version_name is not None:
        validate_single_line(project.version_name, "versionName")
        if len(project.version_name) > 100:
            raise ValueError("versionName must be at most 100 characters")
    _validate_optional_range(
        project.version_code,
        "versionCode",
        minimum=1,
        maximum=2_100_000_000,
    )
    _validate_optional_range(project.compile_sdk, "compileSdk", minimum=35, maximum=99)
    _validate_optional_range(project.min_sdk, "minSdk", minimum=21, maximum=99)
    _validate_optional_range(project.target_sdk, "targetSdk", minimum=21, maximum=99)
    _validate_optional_range(
        project.benchmark_min_sdk,
        "benchmarkMinSdk",
        minimum=23,
        maximum=99,
    )
    _validate_optional_range(project.jvm_target, "jvmTarget", minimum=17, maximum=25)
    if (
        project.min_sdk is not None
        and project.target_sdk is not None
        and project.min_sdk > project.target_sdk
    ):
        raise ValueError("minSdk must not exceed targetSdk")
    if (
        project.target_sdk is not None
        and project.compile_sdk is not None
        and project.target_sdk > project.compile_sdk
    ):
        raise ValueError("targetSdk must not exceed compileSdk")
    if (
        project.min_sdk is not None
        and project.compile_sdk is not None
        and project.min_sdk > project.compile_sdk
    ):
        raise ValueError("minSdk must not exceed compileSdk")
    if (
        project.benchmark_min_sdk is not None
        and project.min_sdk is not None
        and project.benchmark_min_sdk < project.min_sdk
    ):
        raise ValueError("benchmarkMinSdk must not be lower than minSdk")
    if (
        project.benchmark_min_sdk is not None
        and project.compile_sdk is not None
        and project.benchmark_min_sdk > project.compile_sdk
    ):
        raise ValueError("benchmarkMinSdk must not exceed compileSdk")
    if project.posts_backend_url is not None:
        validate_single_line(project.posts_backend_url, "postsBackendUrl")
        if len(project.posts_backend_url) > 2048:
            raise ValueError("postsBackendUrl must be at most 2048 characters")
        parsed_url = urlsplit(project.posts_backend_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError(
                "postsBackendUrl must be an absolute HTTP or HTTPS URL",
            )
        if parsed_url.scheme != "https":
            raise ValueError("postsBackendUrl must use HTTPS")
        if parsed_url.username is not None or parsed_url.password is not None:
            raise ValueError("postsBackendUrl must not contain embedded credentials")
        if parsed_url.query or parsed_url.fragment:
            raise ValueError("postsBackendUrl must not contain a query or fragment")
        if not parsed_url.path.endswith("/"):
            raise ValueError("postsBackendUrl requires a trailing slash")
        if config.starter.remove_examples:
            raise ValueError(
                "postsBackendUrl is available only when example modules are retained",
            )

    unknown = sorted(config.capabilities.difference(CAPABILITY_BY_ID))
    if unknown:
        raise ValueError(f"unknown capabilities: {', '.join(unknown)}")


def _validate_package_identifier(value: str, field_name: str) -> None:
    if not PACKAGE_PATTERN.fullmatch(value):
        raise ValueError(
            f"{field_name} must be a lowercase dotted identifier with at least two segments",
        )
    invalid_segment = next(
        (segment for segment in value.split(".") if segment in RESERVED_WORDS),
        None,
    )
    if invalid_segment is not None:
        raise ValueError(
            f"{field_name} contains reserved keyword '{invalid_segment}'",
        )


def _validate_optional_range(
    value: int | None,
    field_name: str,
    *,
    minimum: int,
    maximum: int,
) -> None:
    if value is not None and not minimum <= value <= maximum:
        raise ValueError(
            f"{field_name} must be between {minimum} and {maximum}",
        )


def resolve_capabilities(
    requested: Iterable[str],
    *,
    remove_examples: bool,
) -> tuple[frozenset[str], dict[str, str]]:
    resolved = set(requested)
    unknown = sorted(resolved.difference(CAPABILITY_BY_ID))
    if unknown:
        raise ValueError(f"unknown capabilities: {', '.join(unknown)}")

    reasons: dict[str, str] = {}
    if not remove_examples:
        for capability_id in sorted(EXAMPLE_REQUIREMENTS):
            if capability_id not in resolved:
                resolved.add(capability_id)
                reasons[capability_id] = "required by the retained example modules"

    changed = True
    while changed:
        changed = False
        for capability_id in sorted(resolved):
            capability = CAPABILITY_BY_ID[capability_id]
            for requirement in capability.requires:
                if requirement not in resolved:
                    resolved.add(requirement)
                    reasons[requirement] = f"required by {capability.title}"
                    changed = True

    return frozenset(resolved), reasons


def with_resolved_capabilities(
    config: SetupConfig,
) -> tuple[SetupConfig, dict[str, str]]:
    requested = config.capabilities
    if config.starter.ai_free:
        requested = requested.difference({"generative_ai"})
    resolved, reasons = resolve_capabilities(
        requested,
        remove_examples=config.starter.remove_examples,
    )
    result = replace(config, capabilities=resolved)
    validate_config(result)
    return result, reasons


def with_resolved_project_settings(
    config: SetupConfig,
    defaults: ProjectSettingsConfig,
) -> SetupConfig:
    requested = config.project_settings
    if (
        requested.jvm_target is not None
        and requested.jvm_target != defaults.jvm_target
    ):
        raise ValueError(
            "jvmTarget is fixed by the repository build-JDK contract",
        )
    identity = replace(
        config.identity,
        application_id=(
            config.identity.application_id or config.identity.package_name
        ),
        display_name=config.identity.display_name or config.identity.project_name,
    )
    resolved = ProjectSettingsConfig(
        version_code=requested.version_code or defaults.version_code,
        version_name=requested.version_name or defaults.version_name,
        compile_sdk=requested.compile_sdk or defaults.compile_sdk,
        min_sdk=requested.min_sdk or defaults.min_sdk,
        target_sdk=requested.target_sdk or defaults.target_sdk,
        benchmark_min_sdk=(
            requested.benchmark_min_sdk or defaults.benchmark_min_sdk
        ),
        jvm_target=requested.jvm_target or defaults.jvm_target,
        posts_backend_url=(
            None
            if config.starter.remove_examples
            else requested.posts_backend_url or defaults.posts_backend_url
        ),
    )
    result = replace(config, identity=identity, project_settings=resolved)
    validate_config(result)
    return result


def config_for_preset(
    identity: IdentityConfig,
    *,
    preset: str,
    output: OutputConfig,
    starter: StarterConfig,
    project_settings: ProjectSettingsConfig | None = None,
    validation: ValidationConfig | None = None,
) -> SetupConfig:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset: {preset}")
    return SetupConfig(
        identity=identity,
        output=output,
        starter=starter,
        project_settings=project_settings or ProjectSettingsConfig(),
        capabilities=PRESETS[preset],
        validation=validation or ValidationConfig(),
    )
