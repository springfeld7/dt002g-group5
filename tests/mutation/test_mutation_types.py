"""Unit tests for mutation_types.py

Validates that MutationAction metadata contracts are correctly enforced.
Covers positive cases, structural violations, and edge cases.
"""

import pytest
from src.transtructiver.mutation.mutation_types import MutationAction, validate_action_metadata


# ===== Helpers =====


def valid_coord():
    """Return a valid coordinate tuple."""
    return (10, 5)


# ===== Positive Cases of Correct Metadata =====


def test_rename_valid_metadata():
    """
    Test that RENAME accepts valid metadata.
    """
    metadata = {"new_val": "renamed_var"}
    assert validate_action_metadata(MutationAction.RENAME, metadata)


def test_insert_valid_metadata():
    """
    Test that INSERT accepts valid metadata.
    """
    metadata = {"new_val": "x = 1", "node_type": "Assign"}
    assert validate_action_metadata(MutationAction.INSERT, metadata)


def test_substitute_valid_metadata():
    """
    Test that SUBSTITUTE accepts properly structured parts_map.
    """
    metadata = {
        "node_type": "For",
        "parts_map": {
            "target": valid_coord(),
            "iterable": valid_coord(),
            "body": valid_coord(),
        },
    }
    assert validate_action_metadata(MutationAction.SUBSTITUTE, metadata)


def test_flatten_valid_metadata():
    """
    Test that FLATTEN accepts valid ref_map.
    """
    metadata = {
        "node_type": "If",
        "ref_map": {
            "entry": valid_coord(),
            "exit": valid_coord(),
        },
    }
    assert validate_action_metadata(MutationAction.FLATTEN, metadata)


# ===== Missing Required Keys =====


@pytest.mark.parametrize(
    "action,metadata",
    [
        (MutationAction.RENAME, {}),
        (MutationAction.INSERT, {"new_val": "x"}),
        (MutationAction.DELETE, {}),
        (MutationAction.SUBSTITUTE, {"node_type": "For"}),
    ],
)
def test_missing_required_keys(action, metadata):
    """
    Test that missing required metadata keys raise ValueError.
    """
    with pytest.raises(ValueError):
        validate_action_metadata(action, metadata)


# ==== Invalid Map Type =====


def test_substitute_parts_map_not_dict():
    """
    Test that SUBSTITUTE fails if parts_map is not a dictionary.
    """
    metadata = {
        "node_type": "For",
        "parts_map": "invalid",
    }

    with pytest.raises(TypeError):
        validate_action_metadata(MutationAction.SUBSTITUTE, metadata)


def test_flatten_ref_map_not_dict():
    """
    Test that FLATTEN fails if ref_map is not a dictionary.
    """
    metadata = {
        "node_type": "If",
        "ref_map": 123,
    }

    with pytest.raises(TypeError):
        validate_action_metadata(MutationAction.FLATTEN, metadata)


# ==== Invalid Coordinate Structure ====


@pytest.mark.parametrize(
    "invalid_coord",
    [
        (1,),  # wrong length
        (1, 2, 3),  # too long
        ("a", "b"),  # wrong types
        (1, "x"),  # mixed types
        None,  # not iterable
    ],
)
def test_invalid_coordinate_shapes(invalid_coord):
    """
    Test that invalid coordinate shapes raise TypeError.
    """
    metadata = {
        "node_type": "For",
        "parts_map": {
            "target": invalid_coord,
            "iterable": (1, 2),
            "body": (3, 4),
        },
    }

    with pytest.raises(TypeError):
        validate_action_metadata(MutationAction.SUBSTITUTE, metadata)


# ==== SUBSTITUTE Strict Key Matching ====


def test_substitute_extra_key_in_parts_map():
    """
    Test that SUBSTITUTE fails if parts_map contains unexpected keys.
    """
    metadata = {
        "node_type": "For",
        "parts_map": {
            "target": (1, 1),
            "iterable": (2, 2),
            "body": (3, 3),
            "extra": (4, 4),
        },
    }

    with pytest.raises(ValueError):
        validate_action_metadata(MutationAction.SUBSTITUTE, metadata)


def test_substitute_missing_key_in_parts_map():
    """
    Test that SUBSTITUTE fails if parts_map is missing required keys.
    """
    metadata = {
        "node_type": "For",
        "parts_map": {
            "target": (1, 1),
            "body": (3, 3),
        },
    }

    with pytest.raises(ValueError):
        validate_action_metadata(MutationAction.SUBSTITUTE, metadata)


# ==== Extra Metadata Keys (Allowed Behavior) ====


def test_extra_top_level_keys_allowed():
    """
    Test that extra top-level metadata keys do not break validation.
    """
    metadata = {
        "new_val": "x",
        "extra": "ignored",
    }

    assert validate_action_metadata(MutationAction.RENAME, metadata)
