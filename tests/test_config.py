from src.transtructiver.config import load_config, resolve_enabled_rules, get_rule_params


def test_load_config_defaults_when_path_none():
    """Test default config loading when path is None."""
    cfg = load_config(None)
    assert cfg.verifier.strictness == "strict"
    assert cfg.transformations == {}


def test_load_config_and_resolve_enabled_rules(tmp_path):
    """Test config loading and rule resolution from file."""
    config_path = tmp_path / "transtructiver.config.json"
    config_path.write_text(
        """
{
  "transformations": {
    "rename-identifier": {
      "enabled": true,
      "params": {
        "level": 2,
        "targets": ["variable"]
      }
    },
    "comment-deletion": {
      "enabled": false
    }
  },
  "verifier": {
    "strictness": "balanced",
    "max_errors": 5
  }
}
""",
        encoding="utf-8",
    )

    cfg = load_config(str(config_path))

    assert cfg.verifier.strictness == "balanced"
    assert cfg.verifier.max_errors == 5

    rules = resolve_enabled_rules(cfg, cli_rules=None)
    assert rules == ["rename-identifier"]

    params = get_rule_params(cfg, "rename-identifier")
    assert params["level"] == 2
    assert params["targets"] == ["variable"]
