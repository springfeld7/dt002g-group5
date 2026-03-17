"""mutation_types.py

Centralized type definitions and constants for the Mutation Engine.
This module defines the shared 'language' used by MutationRules to report 
changes and by the SIVerifier to validate them.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set


class MutationAction(Enum):
    """
    Enumeration of supported transformation action types.

    Members:
        REFORMAT:   Normalizing whitespace, newlines, and existing comments.
        RENAME:     Modifying identifier names (variables/functions).
        DELETE:     Removing specific nodes (e.g., comments).
        INSERT:     Adding brand new synthetic nodes (Dead Code).
        FLATTEN:    Control Flow Flattening via state-machine dispatcher.
        SUBSTITUTE: Logically equivalent structural swaps (e.g., For -> While).
    """

    REFORMAT = auto()  # Normalization (WS/Comments)
    RENAME = auto()  # Variable renaming
    DELETE = auto()  # Comment deletion
    INSERT = auto()  # Dead code injection
    FLATTEN = auto()  # Control Flow Flattening
    SUBSTITUTE = auto()  # Loop substitution

    def __str__(self) -> str:
        """Return the action name as a plain string."""
        return self.name

    @property
    def is_structural(self) -> bool:
        """Returns True if this action alters the tree topology."""
        return self in {
            MutationAction.INSERT,
            MutationAction.DELETE,
            MutationAction.FLATTEN,
            MutationAction.SUBSTITUTE,
        }


# ==== Schema Definitions ====

_ACTION_REQUIRED_KEYS: Dict[MutationAction, List[str]] = {
    MutationAction.REFORMAT: ["new_val"],
    MutationAction.RENAME: ["new_val"],
    MutationAction.DELETE: ["node_type", "content"],
    MutationAction.INSERT: ["new_val", "node_type", "insertion_point"],
    MutationAction.SUBSTITUTE: ["node_type", "parts_map"],
    MutationAction.FLATTEN: ["node_type", "ref_map"],
}

_SUBSTITUTE_REQUIRED_PARTS: Set[str] = {"target", "iterable", "body"}


# ==== Validation Utilities ====


def validate_action_metadata(action: MutationAction, metadata: Dict[str, Any]) -> bool:
    """
    Validate that metadata satisfies the contract of the given action.

    Args:
        action: The mutation action type.
        metadata: Metadata dictionary provided by a MutationRule.

    Raises:
        ValueError: If required keys are missing.
        TypeError: If structure or types are invalid.

    Returns:
        True if validation succeeds.
    """
    required = _ACTION_REQUIRED_KEYS.get(action, [])

    # Presence check
    for key in required:
        if key not in metadata:
            raise ValueError(f"Contract Violation: {action.name} missing required key '{key}'.")

    # Structured validation
    if action == MutationAction.SUBSTITUTE:
        _validate_coord_map(metadata, key="parts_map", expected_keys=_SUBSTITUTE_REQUIRED_PARTS)

    if action == MutationAction.FLATTEN:
        _validate_coord_map(metadata, key="ref_map")

    return True


def _validate_coord_map(
    metadata: Dict[str, Any], key: str, expected_keys: Optional[Set[str]] = None
) -> None:
    """
    Validate a dictionary mapping to (line, col) coordinate tuples.

    Args:
        metadata: Metadata dictionary.
        key: Metadata key to validate.
        expected_keys: Optional exact key set requirement.

    Raises:
        TypeError: If structure or types are invalid.
        ValueError: If expected keys do not match.
    """
    data = metadata.get(key)

    if not isinstance(data, dict):
        raise TypeError(f"'{key}' must be a dict.")

    if expected_keys and set(data.keys()) != expected_keys:
        raise ValueError(f"'{key}' mismatch. Expected keys: {expected_keys}")

    for sub_key, value in data.items():
        if not _is_coord(value):
            raise TypeError(
                f"Invalid coordinate at {key}['{sub_key}']: {value}. " "Expected (int, int)."
            )


def _is_coord(val: Any) -> bool:
    """
    Check whether a value is a valid (line, column) integer tuple.

    Args:
        val: Value to check.

    Returns:
        True if value is a valid coordinate tuple.
    """
    return isinstance(val, (tuple, list)) and len(val) == 2 and all(isinstance(i, int) for i in val)
