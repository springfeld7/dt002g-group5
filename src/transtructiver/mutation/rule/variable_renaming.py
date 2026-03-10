"""variable_renaming.py

Defines VariableRenaming, a concrete MutationRule that renames identifier
nodes in a deterministic way and reports all changes as MutationRecord items.
"""

from typing import Any

from ...node import Node
from ..mutation_rule import MutationRecord, MutationRule
from ..mutation_types import MutationAction, _ACTION_REQUIRED_KEYS


class VariableRenaming(MutationRule):
    """Rename identifier nodes using a generated naming scheme."""

    def __init__(self, level: int = 0) -> None:
        super().__init__()
        self.level = level
        self.scope: list[Any] = []

    def add_appendage(self, node: Node) -> str:
        """Add a suffix to the identifier name."""
        if not node.text:
            return ""

        return f"{node.text}_mut"

    _RENAME_LEVEL = {0: add_appendage}

    def apply(self, root: Node) -> list[MutationRecord]:
        """Apply identifier renaming across the provided tree root."""
        if root is None:
            return []

        rename_by_level = self._RENAME_LEVEL.get(self.level)

        records: list[MutationRecord] = []

        rename_map: dict[str, str] = {}
        for node in root.traverse():
            if node.type != "identifier" or not node.text:
                continue

            original_name = node.text
            if original_name not in rename_map:
                rename_map[original_name] = (
                    rename_by_level(self, node) if rename_by_level else self.add_appendage(node)
                )

            new_name = rename_map[original_name]
            node.text = new_name

            metadata = {"new_val": new_name}
            record = MutationRecord(node.start_point, MutationAction.RENAME, metadata)
            records.append(record)

        return records
