"""External configuration loading and normalization for TranStructIVer.

- External configuration file support
- Transformation toggles and parameters
- Auditor strictness and threshold settings
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass
class TransformationConfig:
    """Configuration for a single mutation rule."""

    enabled: bool = True
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerifierConfig:
    """Verifier strictness and thresholds."""

    strictness: str = "strict"  # strict | balanced | lenient
    max_errors: int | None = None


@dataclass
class AppConfig:
    """Top-level external config shape."""

    transformations: dict[str, TransformationConfig] = field(default_factory=dict)
    verifier: VerifierConfig = field(default_factory=VerifierConfig)
    execution: dict[str, Any] = field(default_factory=dict)


def _load_yaml(path: str) -> dict[str, Any]:
    """Load a YAML config file into a dict.

    Args:
        path (str): Path to the YAML file.

    Returns:
        dict[str, Any]: Parsed YAML data as a dictionary.
    """
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required for --config files. Install with: pip install pyyaml"
        ) from exc

    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data or {}


def _load_json(path: str) -> dict[str, Any]:
    """Load a JSON config file into a dict.

    Args:
        path (str): Path to the JSON file.

    Returns:
        dict[str, Any]: Parsed JSON data as a dictionary.
    """
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data or {}


def _load_toml(path: str) -> dict[str, Any]:
    """Load a TOML config file into a dict.

    Args:
        path (str): Path to the TOML file.

    Returns:
        dict[str, Any]: Parsed TOML data as a dictionary.
    """
    import tomllib

    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    return data or {}


def load_config(path: str | None) -> AppConfig:
    """Load and normalize external config from *path*.

    Args:
        path (str | None): Path to the config file, or None for defaults.

    Returns:
        AppConfig: Loaded and normalized application configuration.
    """
    if not path:
        return AppConfig()

    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        raw = _load_json(path)
    elif suffix == ".toml":
        raw = _load_toml(path)
    else:
        raw = _load_yaml(path)

    # transformations
    transformations: dict[str, TransformationConfig] = {}
    for rule_name, raw_rule in (raw.get("transformations") or {}).items():
        if isinstance(raw_rule, bool):
            transformations[rule_name] = TransformationConfig(enabled=raw_rule)
            continue

        if not isinstance(raw_rule, dict):
            transformations[rule_name] = TransformationConfig(enabled=True)
            continue

        transformations[rule_name] = TransformationConfig(
            enabled=bool(raw_rule.get("enabled", True)),
            params=dict(raw_rule.get("params") or {}),
        )

    # verifier
    raw_verifier = raw.get("verifier") or {}
    verifier = VerifierConfig(
        strictness=str(raw_verifier.get("strictness", "strict")).lower(),
        max_errors=raw_verifier.get("max_errors"),
    )

    # execution (free-form settings used by CLI mapping)
    execution = dict(raw.get("execution") or {})

    return AppConfig(
        transformations=transformations,
        verifier=verifier,
        execution=execution,
    )


def resolve_enabled_rules(config: AppConfig, cli_rules: list[str] | None) -> list[str]:
    """Resolve final rule list from CLI and config.

    Args:
        config (AppConfig): Application configuration object.
        cli_rules (list[str] | None): Rules specified on the CLI, or None.

    Returns:
        list[str]: List of enabled rule names.

    Priority:
        1) Explicit CLI rules
        2) Enabled rules from config.transformations
        3) Default rule: rename-identifier
    """
    if cli_rules:
        return cli_rules

    enabled = [name for name, rule in config.transformations.items() if rule.enabled]
    if enabled:
        return enabled

    return ["rename-identifier"]


def get_rule_params(config: AppConfig, rule_name: str) -> dict[str, Any]:
    """Get per-rule params from config (empty dict if not present).

    Args:
        config (AppConfig): Application configuration object.
        rule_name (str): Name of the rule to get parameters for.

    Returns:
        dict[str, Any]: Dictionary of parameters for the rule.
    """
    rule_cfg = config.transformations.get(rule_name)
    if not rule_cfg:
        return {}
    return dict(rule_cfg.params)
