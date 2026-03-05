"""Unit tests for delete_strategy.py

Validates that DeleteVerificationStrategy correctly audits authorized deletions.
Covers positive case, missing original node, and wrong action in manifest.
"""

from src.transtructiver.verification.strategies.delete_strategy import DeleteVerificationStrategy
from src.transtructiver.mutation.mutation_manifest import ManifestEntry
from src.transtructiver.mutation.mutation_types import MutationAction
from src.transtructiver.node import Node


# ===== Helpers =====


def make_node(type="A", text="val", start=(0, 0), end=(0, 1), children=None):
    return Node(type=type, text=text, start_point=start, end_point=end, children=children or [])


# ===== Positive Case =====


def test_valid_delete():
    """Should return empty list when deletion is authorized."""
    orig = make_node(type="Var", text="x")
    entry = ManifestEntry(
        original_id=orig.start_point, history=[{"action": MutationAction.DELETE}], metadata={}
    )

    strategy = DeleteVerificationStrategy()
    errs = strategy.verify(orig, None, entry)
    assert errs == []


# ===== Missing Original Node =====


def test_missing_original_node():
    """Should return error if original node is None."""
    entry = ManifestEntry(
        original_id=(0, 0), history=[{"action": MutationAction.DELETE}], metadata={}
    )

    strategy = DeleteVerificationStrategy()
    errs = strategy.verify(None, None, entry)
    assert len(errs) == 1
    assert "missing original node" in errs[0]


# ===== Wrong Action in Manifest =====


def test_wrong_manifest_action():
    """Should return error if last action is not DELETE."""
    orig = make_node(type="Var", text="x")
    entry = ManifestEntry(
        original_id=orig.start_point, history=[{"action": MutationAction.RENAME}], metadata={}
    )

    strategy = DeleteVerificationStrategy()
    errs = strategy.verify(orig, None, entry)
    assert len(errs) == 1
    assert "Unauthorized deletion" in errs[0]
