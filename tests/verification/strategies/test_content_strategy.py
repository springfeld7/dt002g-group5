"""Unit tests for content_strategy.py

Validates that ContentVerificationStrategy correctly verifies REFORMAT and RENAME actions.
Covers positive cases, missing metadata, type mismatches, and content mismatches.
"""

import pytest
from src.transtructiver.verification.strategies.content_strategy import ContentVerificationStrategy
from src.transtructiver.mutation.mutation_manifest import ManifestEntry
from src.transtructiver.node import Node


# ===== Helpers =====


def make_node(type="A", text="val", start=(0, 0), end=(0, 1), children=None):
    return Node(type=type, text=text, start_point=start, end_point=end, children=children or [])


# ===== Positive Cases =====


def test_valid_content():
    """
    Should return empty error list when content matches 'new_val' and types match.
    """
    orig = make_node(type="Var", text="x")
    mut = make_node(type="Var", text="y")
    entry = ManifestEntry(original_id=orig.start_point, history=[], metadata={"new_val": "y"})

    strategy = ContentVerificationStrategy()
    errs = strategy.verify(orig, mut, entry)
    assert errs == []


# ===== Missing 'new_val' in metadata =====


def test_missing_new_val():
    orig = make_node(type="Var", text="x")
    mut = make_node(type="Var", text="y")
    entry = ManifestEntry(original_id=orig.start_point, history=[], metadata={})

    strategy = ContentVerificationStrategy()
    errs = strategy.verify(orig, mut, entry)
    assert len(errs) == 1
    assert "Missing 'new_val'" in errs[0]


# ===== None node handling =====


@pytest.mark.parametrize(
    "orig,mut",
    [
        (None, make_node(type="Var", text="y")),
        (make_node(type="Var", text="x"), None),
        (None, None),
    ],
)
def test_none_nodes(orig, mut):
    entry = ManifestEntry(original_id=(0, 0), history=[], metadata={"new_val": "x"})
    strategy = ContentVerificationStrategy()
    errs = strategy.verify(orig, mut, entry)
    assert len(errs) == 1
    assert "received a None node" in errs[0]


# ===== Type mismatch =====


def test_type_mismatch():
    orig = make_node(type="Var", text="x")
    mut = make_node(type="Const", text="x")
    entry = ManifestEntry(original_id=orig.start_point, history=[], metadata={"new_val": "x"})

    strategy = ContentVerificationStrategy()
    errs = strategy.verify(orig, mut, entry)
    assert len(errs) == 1
    assert "Type mismatch" in errs[0]


# ===== Content mismatch =====


def test_content_mismatch():
    orig = make_node(type="Var", text="x")
    mut = make_node(type="Var", text="y")
    entry = ManifestEntry(original_id=orig.start_point, history=[], metadata={"new_val": "z"})

    strategy = ContentVerificationStrategy()
    errs = strategy.verify(orig, mut, entry)
    assert len(errs) == 1
    assert "Content mismatch" in errs[0]
