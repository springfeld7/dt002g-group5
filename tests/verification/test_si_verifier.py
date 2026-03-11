"""Unit tests for si_verifier.py

Covers verification of aligned trees, synchronized trees, deletions, insertions,
identity checks, strategy dispatch, and edge cases.
"""

import csv
import pytest
from src.transtructiver.verification.si_verifier import SIVerifier
from src.transtructiver.node import Node
from src.transtructiver.mutation.mutation_manifest import MutationManifest
from src.transtructiver.mutation.mutation_types import MutationAction


# ===== Test Setup and Helpers =====


@pytest.fixture
def verifier():
    """Provides a fresh SIVerifier instance for each test."""
    return SIVerifier()


def make_node(type="A", text="val", start=(0, 0), end=(0, 1), children=None):
    """Helper to create a Node with specified attributes."""
    return Node(type=type, text=text, start_point=start, end_point=end, children=children or [])


def make_tree_with_children(children_specs):
    """
    Build a Node tree from a list of (type, text, start, end) tuples.
    Returns root node with the specified children.
    """
    root = make_node(type="module", text="")
    for spec in children_specs:
        node = make_node(*spec)
        root.children.append(node)
    return root


def build_manifest(entries):
    """
    Build a MutationManifest from a list of tuples:
    (node_id, action, metadata, rule_name)
    """
    manifest = MutationManifest()
    for node_id, action, metadata, rule_name in entries:
        manifest.add_entry(node_id=node_id, action=action, metadata=metadata, rule_name=rule_name)
    return manifest


# ===== Positive Cases =====


def test_verify_aligned_identity():
    """Should succeed when the mutated tree is identical to the original."""
    assign = ("assignment", "x = 1", (0, 2), (0, 5))
    call = ("call", "print(x)", (1, 0), (1, 8))
    root_orig = make_tree_with_children([assign, call])
    root_mut = root_orig.clone()
    manifest = MutationManifest()
    verifier = SIVerifier()
    assert verifier.verify(root_orig, root_mut, manifest)
    assert verifier.errors == []


def test_verify_aligned_reformat_and_rename():
    """Should succeed when reformat and rename are authorized in manifest."""
    assign_orig = ("assignment", "x = 1", (0, 2), (0, 5))
    call_orig = ("call", "print(x)", (1, 0), (1, 8))
    root_orig = make_tree_with_children([assign_orig, call_orig])

    assign_mut = make_node("assignment", "x=1", start=(0, 2), end=(0, 5))
    call_mut = make_node("call", "print(y)", start=(1, 0), end=(1, 8))
    root_mut = make_node("module", "")
    root_mut.children.extend([assign_mut, call_mut])

    manifest = build_manifest(
        [
            ((0, 2), MutationAction.REFORMAT, {"new_val": "x=1"}, "reformat_rule"),
            ((1, 0), MutationAction.RENAME, {"new_val": "print(y)"}, "rename_rule"),
        ]
    )

    verifier = SIVerifier()
    assert verifier.verify(root_orig, root_mut, manifest)
    assert verifier.errors == []


def test_verify_insert_node():
    """Should succeed when an inserted node is authorized in manifest."""
    assign = ("assignment", "x = 1", (0, 2), (0, 5))
    root_orig = make_tree_with_children([assign])

    inserted = make_node("call", "print(x)", start=(-1, 0), end=(1, 8))
    root_mut = make_node("module", "")
    root_mut.children.extend([make_node(*assign), inserted])

    manifest = build_manifest(
        [
            (
                (-1, 0),
                MutationAction.INSERT,
                {"new_val": "print(x)", "node_type": "call"},
                "insert_rule",
            ),
        ]
    )

    verifier = SIVerifier()
    assert verifier.verify(root_orig, root_mut, manifest)
    assert verifier.errors == []


def test_verify_delete_node():
    """Should succeed when a deletion is authorized in the manifest."""
    assign = ("assignment", "x = 1", (0, 2), (0, 5))
    call = ("call", "print(x)", (1, 0), (1, 8))
    root_orig = make_tree_with_children([assign, call])

    root_mut = make_tree_with_children([assign])  # call deleted

    manifest = build_manifest(
        [
            ((1, 0), MutationAction.DELETE, {}, "delete_rule"),
        ]
    )

    verifier = SIVerifier()
    assert verifier.verify(root_orig, root_mut, manifest)
    assert verifier.errors == []


# ===== Composite Mutation Case =====


def test_verify_composite_mutations():
    """Should succeed when multiple mutations (reformat, rename, insert, delete) are authorized."""
    root_orig = make_node("module", "")
    func_orig = make_node("function_def", "def foo():", start=(0, 2), end=(0, 10))
    assign_orig = make_node("assignment", "x = 1", start=(1, 2), end=(1, 7))
    call_orig = make_node("call", "print(x)", start=(2, 2), end=(2, 10))
    root_orig.children.append(func_orig)
    func_orig.children.extend([assign_orig, call_orig])

    root_mut = make_node("module", "")
    func_mut = make_node("function_def", "def foo():", start=(0, 2), end=(0, 10))
    assign_mut = make_node("assignment", "x=1", start=(1, 2), end=(1, 7))  # reformat
    call_mut = make_node("call", "print(y)", start=(2, 2), end=(2, 10))  # rename
    inserted_var = make_node("assignment", "y = 2", start=(-1, 0), end=(0, 0))  # insert
    root_mut.children.append(func_mut)
    func_mut.children.extend([assign_mut, call_mut, inserted_var])

    manifest = build_manifest(
        [
            ((1, 2), MutationAction.REFORMAT, {"new_val": "x=1"}, "reformat_rule"),
            ((2, 2), MutationAction.RENAME, {"new_val": "print(y)"}, "rename_rule"),
            (
                (-1, 0),
                MutationAction.INSERT,
                {"new_val": "y = 2", "node_type": "assignment"},
                "insert_rule",
            ),
            ((3, 0), MutationAction.DELETE, {}, "delete_rule"),
        ]
    )

    verifier = SIVerifier()
    assert verifier.verify(root_orig, root_mut, manifest)
    assert verifier.errors == []


# ===== Unauthorized Change Case =====


def test_verify_aligned_reformat_and_rename_without_manifest():
    """Should fail when tree changes exist but manifest is empty."""
    assign_orig = ("assignment", "x = 1", (0, 2), (0, 5))
    call_orig = ("call", "print(x)", (1, 0), (1, 8))
    root_orig = make_tree_with_children([assign_orig, call_orig])

    assign_mut = make_node("assignment", "x=1", start=(0, 2), end=(0, 5))
    call_mut = make_node("call", "print(y)", start=(1, 0), end=(1, 8))
    root_mut = make_node("module", "")
    root_mut.children.extend([assign_mut, call_mut])

    manifest = MutationManifest()  # empty

    verifier = SIVerifier()
    result = verifier.verify(root_orig, root_mut, manifest)
    assert result is False
    assert len(verifier.errors) > 0


def test_verify_insert_node_without_manifest():
    """Should fail when a synthetic (inserted) node exists but the manifest has no entry."""
    # Original CST
    root_orig = make_node(type="module", text="")

    # Mutated CST: synthetic node added
    root_mut = make_node(type="module", text="")
    inserted_call = make_node(type="call", text="print(x)", start=(-1, 0), end=(-1, 8))
    root_mut.children.append(inserted_call)

    # Empty manifest
    manifest = MutationManifest()

    verifier = SIVerifier()
    result = verifier.verify(root_orig, root_mut, manifest)

    # Should fail because INSERT was not authorized
    assert result is False
    assert len(verifier.errors) > 0


def test_verify_delete_node_without_manifest():
    """Should fail when a node is deleted but the manifest does not authorize it."""
    # Original CST
    root_orig = make_node(type="module", text="")
    assign_orig = make_node(type="assignment", text="x = 1", start=(0, 0), end=(0, 5))
    func_call_orig = make_node(type="call", text="print(x)", start=(1, 0), end=(1, 8))
    root_orig.children.extend([assign_orig, func_call_orig])

    # Mutated CST: deletion of the function call
    root_mut = make_node(type="module", text="")
    root_mut.children.append(assign_orig.clone())  # call removed

    # Empty manifest (no DELETE recorded)
    manifest = MutationManifest()

    verifier = SIVerifier()
    result = verifier.verify(root_orig, root_mut, manifest)

    # Should fail because deletion is not authorized
    assert result is False
    assert len(verifier.errors) > 0


# ===== Edge Cases =====


def test_verify_empty_trees():
    """Should succeed when both original and mutated trees are empty."""
    root_orig = make_node("module", "")
    root_mut = make_node("module", "")
    manifest = MutationManifest()
    verifier = SIVerifier()
    assert verifier.verify(root_orig, root_mut, manifest)
    assert verifier.errors == []


def test_verify_node_without_text_or_children():
    """Should succeed when nodes have empty text and no children."""
    root_orig = make_node("module", "")
    empty_node = make_node("block", "", start=(0, 0), end=(0, 0))
    root_orig.children.append(empty_node)
    root_mut = root_orig.clone()
    manifest = MutationManifest()
    verifier = SIVerifier()
    assert verifier.verify(root_orig, root_mut, manifest)
    assert verifier.errors == []


# ===== Test Summary Logging =====


def test_write_summary_creates_file(verifier, tmp_path):
    log_file = tmp_path / "summary_log.csv"
    snippet_id = "snippet_1"
    verified = True

    verifier.write_summary(snippet_id, verified, log_path=str(log_file))

    # File should exist
    assert log_file.exists()

    # Read CSV content
    with open(log_file, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows[0][0] == snippet_id
    assert rows[0][1] == "1"
    assert rows[0][2] == ""
