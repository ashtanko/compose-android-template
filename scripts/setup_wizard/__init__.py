"""Project setup wizard shared by the command-line and browser interfaces."""

from .engine import SetupError, SetupPlan, apply_plan, build_plan
from .model import (
    CAPABILITIES,
    PRESETS,
    IdentityConfig,
    OutputConfig,
    SetupConfig,
    StarterConfig,
    ValidationConfig,
)

__all__ = [
    "CAPABILITIES",
    "PRESETS",
    "IdentityConfig",
    "OutputConfig",
    "SetupConfig",
    "SetupError",
    "SetupPlan",
    "StarterConfig",
    "ValidationConfig",
    "apply_plan",
    "build_plan",
]
