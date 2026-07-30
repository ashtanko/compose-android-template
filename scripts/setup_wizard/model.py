"""Configuration schema and capability resolution for the setup wizard."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
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
    plugin_alias: str | None = None
    author: str | None = None


@dataclass(frozen=True)
class OutputConfig:
    mode: str = "copy"
    path: str | None = None


@dataclass(frozen=True)
class StarterConfig:
    remove_examples: bool = True


@dataclass(frozen=True)
class ValidationConfig:
    format: bool = False
    level: str = "none"


@dataclass(frozen=True)
class SetupConfig:
    identity: IdentityConfig
    output: OutputConfig = field(default_factory=OutputConfig)
    starter: StarterConfig = field(default_factory=StarterConfig)
    capabilities: frozenset[str] = field(default_factory=frozenset)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SetupConfig":
        if not isinstance(value, dict):
            raise ValueError("configuration must be a JSON object")
        schema_version = value.get("schemaVersion", SCHEMA_VERSION)
        if schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schemaVersion {schema_version}; expected {SCHEMA_VERSION}",
            )

        identity_value = _object(value, "identity")
        output_value = _object(value, "output", required=False)
        starter_value = _object(value, "starter", required=False)
        validation_value = _object(value, "validation", required=False)
        raw_capabilities = value.get("capabilities", [])
        if not isinstance(raw_capabilities, list) or not all(
            isinstance(item, str) for item in raw_capabilities
        ):
            raise ValueError("capabilities must be an array of capability IDs")

        config = cls(
            identity=IdentityConfig(
                package_name=_string(identity_value, "packageName"),
                project_name=_string(identity_value, "projectName"),
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
            ),
            capabilities=frozenset(raw_capabilities),
            validation=ValidationConfig(
                format=_boolean(validation_value, "format", default=False),
                level=_string(validation_value, "level", default="none"),
            ),
            schema_version=schema_version,
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
                "pluginAlias": self.identity.plugin_alias,
                "author": self.identity.author,
            },
            "output": {
                "mode": self.output.mode,
                "path": self.output.path,
            },
            "starter": {
                "removeExamples": self.starter.remove_examples,
            },
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
    if not PACKAGE_PATTERN.fullmatch(identity.package_name):
        raise ValueError(
            "packageName must be a lowercase dotted identifier with at least two segments",
        )
    invalid_segment = next(
        (
            segment
            for segment in identity.package_name.split(".")
            if segment in RESERVED_WORDS
        ),
        None,
    )
    if invalid_segment is not None:
        raise ValueError(f"packageName contains reserved keyword '{invalid_segment}'")

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

    if config.output.mode not in {"copy", "inPlace"}:
        raise ValueError("output.mode must be 'copy' or 'inPlace'")
    if config.output.mode == "copy" and not config.output.path:
        raise ValueError("output.path is required in copy mode")
    if config.output.mode == "inPlace" and config.output.path:
        raise ValueError("output.path must be omitted in inPlace mode")
    if config.validation.level not in {"none", "narrow", "full"}:
        raise ValueError("validation.level must be none, narrow, or full")

    unknown = sorted(config.capabilities.difference(CAPABILITY_BY_ID))
    if unknown:
        raise ValueError(f"unknown capabilities: {', '.join(unknown)}")


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
    resolved, reasons = resolve_capabilities(
        config.capabilities,
        remove_examples=config.starter.remove_examples,
    )
    result = replace(config, capabilities=resolved)
    validate_config(result)
    return result, reasons


def config_for_preset(
    identity: IdentityConfig,
    *,
    preset: str,
    output: OutputConfig,
    starter: StarterConfig,
    validation: ValidationConfig | None = None,
) -> SetupConfig:
    if preset not in PRESETS:
        raise ValueError(f"unknown preset: {preset}")
    return SetupConfig(
        identity=identity,
        output=output,
        starter=starter,
        capabilities=PRESETS[preset],
        validation=validation or ValidationConfig(),
    )
