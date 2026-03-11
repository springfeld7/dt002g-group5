"""Unit tests for mutation_engine.py

Validates that MutationEngine correctly applies MutationRules, aggregates
MutationRecords into a MutationManifest, and tracks history and metadata
across multiple rules and nodes.
"""

from unittest.mock import MagicMock
from src.transtructiver.mutation.mutation_engine import MutationEngine
from src.transtructiver.mutation.mutation_manifest import MutationManifest
from src.transtructiver.mutation.rules.mutation_rule import MutationRecord
from src.transtructiver.mutation.mutation_types import MutationAction
from src.transtructiver.node import Node


# ===== Helpers =====


def make_mock_rule(name, returned_records):
    """
    Return a MagicMock MutationRule with a given name and a fixed apply() result.
    """
    rule = MagicMock()
    rule.name = name
    rule.apply.return_value = returned_records
    return rule


def make_valid_node(start=(0, 0), end=(0, 1), node_type="Dummy"):
    """
    Return a minimal valid Node instance for testing purposes.
    """
    return Node(start_point=start, end_point=end, type=node_type)


def make_sample_record(node_id=(0, 1), action=MutationAction.RENAME, metadata=None):
    """
    Return a sample MutationRecord-like object (dict or dataclass).
    """
    record = MagicMock(spec=MutationRecord)
    record.node_id = node_id
    record.action = action
    record.metadata = metadata or {}
    return record


# ===== Positive Cases =====


def test_apply_mutations_creates_manifest():
    """
    Test that apply_mutations returns a MutationManifest instance.
    """
    node = make_valid_node()
    engine = MutationEngine([])

    manifest = engine.apply_mutations(node)

    assert isinstance(manifest, MutationManifest)


def test_single_rule_applied_and_manifest_populated():
    """
    Test that a single rule produces entries in the manifest.
    """
    node = make_valid_node()
    record = make_sample_record(node_id=(1, 1), metadata={"x": 1})
    rule = make_mock_rule("RuleA", [record])
    engine = MutationEngine([rule])

    manifest = engine.apply_mutations(node)

    entry = manifest.get_entry((1, 1))
    assert entry is not None
    assert entry.metadata["x"] == 1
    assert entry.history[0]["rule"] == "RuleA"
    assert entry.history[0]["action"] == record.action


def test_multiple_rules_applied_sequentially():
    """
    Test that multiple rules are applied in sequence and all updates are tracked.
    """
    node = make_valid_node()
    record1 = make_sample_record(node_id=(1, 1), metadata={"a": 1})
    record2 = make_sample_record(node_id=(1, 1), action=MutationAction.INSERT, metadata={"b": 2})
    rule1 = make_mock_rule("RuleA", [record1])
    rule2 = make_mock_rule("RuleB", [record2])
    engine = MutationEngine([rule1, rule2])

    manifest = engine.apply_mutations(node)

    entry = manifest.get_entry((1, 1))
    assert entry.metadata["a"] == 1
    assert entry.metadata["b"] == 2
    assert entry.history[0]["rule"] == "RuleA"
    assert entry.history[1]["rule"] == "RuleB"


def test_metadata_overwrites_on_conflict():
    """
    Test that sequential updates to the same node's metadata follow
    Last-In-First-Out (LIFO) merging logic.
    """
    node = make_valid_node()
    # Assume both records target the same node (0, 1)
    rec1 = make_sample_record(node_id=(0, 1), metadata={"status": "old"})
    rec2 = make_sample_record(node_id=(0, 1), metadata={"status": "new"})

    engine = MutationEngine([make_mock_rule("R1", [rec1]), make_mock_rule("R2", [rec2])])

    manifest = engine.apply_mutations(node)

    entry = manifest.get_entry((0, 1))
    assert entry.metadata["status"] == "new"
    assert len(entry.history) == 2


def test_multiple_nodes_handled_correctly():
    """
    Test that mutations for different nodes are tracked independently.
    """
    node = make_valid_node()
    record1 = make_sample_record(node_id=(1, 1), metadata={"x": 1})
    record2 = make_sample_record(node_id=(2, 2), metadata={"y": 2})
    rule = make_mock_rule("RuleX", [record1, record2])
    engine = MutationEngine([rule])

    manifest = engine.apply_mutations(node)

    entry1 = manifest.get_entry((1, 1))
    entry2 = manifest.get_entry((2, 2))
    assert entry1.metadata["x"] == 1
    assert entry2.metadata["y"] == 2
    assert entry1.original_id != entry2.original_id


# ===== Edge Cases =====


def test_no_rules_returns_empty_manifest():
    """Test that an engine with no rules returns an empty manifest."""
    node = make_valid_node()
    engine = MutationEngine([])
    manifest = engine.apply_mutations(node)
    assert manifest._entries == {}


def test_rule_returns_empty_changes_list():
    """Test that a rule returning an empty list does not affect the manifest."""
    node = make_valid_node()
    rule = make_mock_rule("EmptyRule", [])
    engine = MutationEngine([rule])
    manifest = engine.apply_mutations(node)
    assert manifest._entries == {}


def test_conflicting_updates_to_same_node():
    """
    Test that sequential updates to the same node from different rules
    are both applied and reflected in history and metadata.
    """
    node = make_valid_node()
    rec1 = make_sample_record(node_id=(1, 1), action=MutationAction.RENAME, metadata={"v": 1})
    rec2 = make_sample_record(node_id=(1, 1), action=MutationAction.INSERT, metadata={"v": 2})
    rule1 = make_mock_rule("R1", [rec1])
    rule2 = make_mock_rule("R2", [rec2])
    engine = MutationEngine([rule1, rule2])
    manifest = engine.apply_mutations(node)
    entry = manifest.get_entry((1, 1))
    assert entry.metadata["v"] == 2
    assert entry.history[0]["rule"] == "R1"
    assert entry.history[1]["rule"] == "R2"


def test_rule_name_used_even_if_action_none():
    """Test that rule_name is still recorded if action is None."""
    node = make_valid_node()
    rec = make_sample_record(node_id=(1, 1), action=None)
    rule = make_mock_rule("RuleNone", [rec])
    engine = MutationEngine([rule])
    manifest = engine.apply_mutations(node)
    entry = manifest.get_entry((1, 1))
    assert entry.history[0]["rule"] == "RuleNone"
    assert entry.history[0]["action"] is None
