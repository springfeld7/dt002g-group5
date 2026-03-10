"""
Unit tests for mutation_manifest.py

Validates that MutationManifest and ManifestEntry correctly track mutations,
merge metadata, and maintain audit history. Covers positive cases, repeated
updates, and edge cases.
"""

import pytest
from src.transtructiver.mutation.mutation_manifest import MutationManifest, ManifestEntry
from src.transtructiver.mutation.mutation_types import MutationAction


# ===== Helpers =====


def sample_node_id():
    """Return a sample node identifier."""
    return (3, 7)


def sample_metadata():
    """Return sample metadata for testing."""
    return {"new_val": "x", "node_type": "Assign"}


# ===== ManifestEntry Positive Cases =====


def test_manifest_entry_initialization():
    """Test that a ManifestEntry is correctly initialized."""
    node_id = sample_node_id()
    entry = ManifestEntry(original_id=node_id)
    assert entry.original_id == node_id
    assert entry.history == []
    assert entry.metadata == {}


def test_manifest_entry_update_appends_history_and_merges_metadata():
    """
    Test that update() appends rule/action to history and merges metadata.
    """
    entry = ManifestEntry(original_id=sample_node_id())
    entry.update(metadata={"foo": 123}, rule_name="RuleA", action=MutationAction.RENAME)
    assert len(entry.history) == 1
    assert entry.history[0]["rule"] == "RuleA"
    assert entry.history[0]["action"] == MutationAction.RENAME
    assert entry.metadata["foo"] == 123


def test_manifest_entry_update_overwrites_existing_keys():
    """
    Test that update() overwrites keys in metadata but keeps others intact.
    """
    entry = ManifestEntry(original_id=sample_node_id(), metadata={"foo": 1, "bar": 2})
    entry.update(metadata={"foo": 99, "baz": 3}, rule_name="RuleB", action=MutationAction.INSERT)
    assert entry.metadata["foo"] == 99  # overwritten
    assert entry.metadata["bar"] == 2  # preserved
    assert entry.metadata["baz"] == 3  # added


# ===== MutationManifest Tests =====


@pytest.fixture
def manifest():
    """Fixture to provide a fresh MutationManifest for each test."""
    return MutationManifest()


def test_add_entry_creates_new_entry(manifest):
    """
    Test that adding a mutation creates a new ManifestEntry if none exists.
    """
    node_id = sample_node_id()
    manifest.add_entry(node_id, MutationAction.RENAME, {"a": 1}, "RuleX")
    entry = manifest.get_entry(node_id)
    assert isinstance(entry, ManifestEntry)
    assert entry.original_id == node_id
    assert entry.history[0]["rule"] == "RuleX"
    assert entry.history[0]["action"] == MutationAction.RENAME
    assert entry.metadata["a"] == 1


def test_add_entry_updates_existing_entry(manifest):
    """
    Test that adding a mutation to an existing entry updates it correctly.
    """
    node_id = sample_node_id()
    manifest.add_entry(node_id, MutationAction.RENAME, {"foo": 1}, "RuleA")
    manifest.add_entry(node_id, MutationAction.INSERT, {"bar": 2}, "RuleB")
    entry = manifest.get_entry(node_id)
    assert len(entry.history) == 2
    assert entry.history[0]["rule"] == "RuleA"
    assert entry.history[1]["rule"] == "RuleB"
    assert entry.metadata["foo"] == 1
    assert entry.metadata["bar"] == 2


def test_get_entry_returns_none_for_unknown_node(manifest):
    """
    Test that get_entry() returns None for a node with no mutations.
    """
    assert manifest.get_entry((999, 999)) is None


# ===== Multiple Nodes =====


def test_manifest_tracks_multiple_nodes_independently(manifest):
    """
    Test that multiple nodes are tracked independently in the manifest.
    """
    manifest.add_entry((1, 1), MutationAction.RENAME, {"x": 1}, "R1")
    manifest.add_entry((2, 2), MutationAction.INSERT, {"y": 2}, "R2")
    entry1 = manifest.get_entry((1, 1))
    entry2 = manifest.get_entry((2, 2))
    assert entry1.metadata["x"] == 1
    assert entry2.metadata["y"] == 2
    assert entry1.original_id != entry2.original_id
    assert len(entry1.history) == 1
    assert len(entry2.history) == 1


# ===== Data Integrity & Isolation =====


def test_metadata_deep_copy_isolation(manifest):
    """
    Test that modifying a dictionary after passing it to the manifest
    does not affect the stored entry (prevents shared-reference side effects).
    """
    node_id = (10, 10)
    original_meta = {"tags": ["original"], "info": {"version": 1}}

    manifest.add_entry(node_id, MutationAction.RENAME, original_meta, "Rule1")

    # Simulate external code modifying the dict after the call
    original_meta["tags"].append("corrupted")
    original_meta["info"]["version"] = 99

    entry = manifest.get_entry(node_id)
    assert "corrupted" not in entry.metadata["tags"]
    assert entry.metadata["info"]["version"] == 1


def test_metadata_merge_does_not_mutate_previous_history(manifest):
    """
    Test that updating metadata creates a new state and doesn't
    retroactively change nested structures in previous history logs.
    """
    node_id = (5, 5)

    manifest.add_entry(node_id, MutationAction.INSERT, {"data": [1]}, "RuleA")
    manifest.add_entry(node_id, MutationAction.INSERT, {"data": [1, 2]}, "RuleB")

    entry = manifest.get_entry(node_id)
    # Even if they share the same key 'data', we want to ensure
    # the dictionary merge logic hasn't created a shared reference.
    assert entry.metadata["data"] == [1, 2]


# ===== Conflict & State Logic =====


def test_action_sequence_integrity(manifest):
    """
    Test that the history preserves the exact chronological order of
    conflicting actions (e.g., RENAME then DELETE).
    """
    node_id = (1, 1)

    manifest.add_entry(node_id, MutationAction.RENAME, {"name": "new"}, "Rule1")
    manifest.add_entry(node_id, MutationAction.DELETE, {}, "Rule2")

    entry = manifest.get_entry(node_id)
    assert entry.history[0]["action"] == MutationAction.RENAME
    assert entry.history[1]["action"] == MutationAction.DELETE


def test_add_entry_with_empty_metadata(manifest):
    """
    Test that adding a mutation with an empty metadata dictionary
    still records the history event without wiping existing metadata.
    """
    node_id = (1, 2)

    manifest.add_entry(node_id, MutationAction.RENAME, {"key": "val"}, "Rule1")
    manifest.add_entry(node_id, MutationAction.RENAME, {}, "Rule2")

    entry = manifest.get_entry(node_id)
    assert len(entry.history) == 2
    assert entry.metadata["key"] == "val"


# ===== Structural Gear Shift Tests =====


def test_initial_structural_state(manifest):
    """Ensure a fresh manifest starts clean and non-structural."""
    assert manifest.has_structural_changes() is False


def test_content_change_does_not_trigger_structural_flag(manifest):
    """RENAME and REFORMAT should keep the manifest in 'Fast Path' mode."""
    manifest.add_entry((10, 5), MutationAction.RENAME, {"new_val": "var"}, "Rule")
    assert manifest.has_structural_changes() is False


def test_structural_change_triggers_flag(manifest):
    """A single DELETE should flip the manifest to structural mode."""
    manifest.add_entry((20, 0), MutationAction.DELETE, {"node_type": "comment"}, "Rule")
    assert manifest.has_structural_changes() is True


def test_structural_flag_is_persistent(manifest):
    """Once structural, the flag must stay True regardless of subsequent actions."""
    manifest.add_entry((5, 5), MutationAction.INSERT, {"node_type": "pass"}, "Rule1")
    assert manifest.has_structural_changes() is True

    manifest.add_entry((6, 6), MutationAction.REFORMAT, {"new_val": " "}, "Rule2")
    assert manifest.has_structural_changes() is True


# ===== Edge Cases =====


def test_multiple_updates_with_same_rule(manifest):
    """
    Test that multiple updates with the same rule are recorded separately.
    """
    node_id = sample_node_id()
    manifest.add_entry(node_id, MutationAction.RENAME, {"x": 1}, "RuleA")
    manifest.add_entry(node_id, MutationAction.RENAME, {"y": 2}, "RuleA")

    entry = manifest.get_entry(node_id)
    assert len(entry.history) == 2
    assert entry.metadata["x"] == 1
    assert entry.metadata["y"] == 2


def test_metadata_merge_with_overlapping_keys(manifest):
    """
    Test that overlapping metadata keys are overwritten, not removed.
    """
    node_id = sample_node_id()
    manifest.add_entry(node_id, MutationAction.RENAME, {"val": 10}, "RuleA")
    manifest.add_entry(node_id, MutationAction.RENAME, {"val": 20}, "RuleB")

    entry = manifest.get_entry(node_id)
    assert entry.metadata["val"] == 20  # latest overwrites previous


def test_history_and_metadata_consistency(manifest):
    """
    Ensure that each update correctly appends to history and merges metadata
    without losing prior information.
    """
    node_id = sample_node_id()
    manifest.add_entry(node_id, MutationAction.RENAME, {"a": 1}, "R1")
    manifest.add_entry(node_id, MutationAction.INSERT, {"b": 2}, "R2")

    entry = manifest.get_entry(node_id)
    assert entry.history[0]["rule"] == "R1"
    assert entry.history[1]["rule"] == "R2"
    assert entry.history[0]["action"] == MutationAction.RENAME
    assert entry.history[1]["action"] == MutationAction.INSERT
    assert entry.metadata == {"a": 1, "b": 2}
