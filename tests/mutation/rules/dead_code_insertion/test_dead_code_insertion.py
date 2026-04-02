"""Unit tests for the DeadCodeInsertionRule mutation rule.

This suite validates core behavior, determinism, fallback guarantees,
and structural correctness of dead code insertion within CSTs.
"""

import pytest

from transtructiver.mutation.rules.dead_code_insertion.dead_code_insertion import (
    DeadCodeInsertionRule,
)
from src.transtructiver.node import Node
from src.transtructiver.mutation.mutation_context import MutationContext


# ===== Helpers =====


def _wire_parents(node: Node, parent: Node | None = None) -> Node:
    """Recursively populate parent links after literal tree construction."""
    node.parent = parent
    for child in node.children:
        _wire_parents(child, node)
    return node


def label_basic_block_tree(root: Node) -> Node:
    """Annotate minimal semantic labels required for dead code insertion."""
    _wire_parents(root)

    root.semantic_label = "root"
    root.language = "python"

    for node in root.traverse():
        if node.type == "function_definition":
            node.semantic_label = "function_scope"
        elif node.type == "block":
            node.semantic_label = "block_scope"

    return root


def make_simple_block_tree() -> Node:
    """Create a minimal function with a block and one statement."""
    stmt = Node((2, 4), (2, 10), "expression", text="x = 1")

    block = Node((1, 0), (3, 0), "block", children=[stmt])

    root = Node(
        (0, 0),
        (3, 0),
        "module",
        children=[Node((0, 0), (3, 0), "function_definition", children=[block])],
    )

    return label_basic_block_tree(root)


def make_empty_block_tree() -> Node:
    """Create a block with no children (edge case)."""
    block = Node((1, 0), (2, 0), "block", children=[])

    root = Node(
        (0, 0),
        (2, 0),
        "module",
        children=[Node((0, 0), (2, 0), "function_definition", children=[block])],
    )

    return label_basic_block_tree(root)


# ===== Fixtures =====


@pytest.fixture
def mutation_context() -> MutationContext:
    """Provide a fresh MutationContext for tests."""
    return MutationContext()


@pytest.fixture
def simple_block_tree() -> Node:
    """Provide a minimal valid tree with one insertion point."""
    return make_simple_block_tree()


@pytest.fixture
def empty_block_tree() -> Node:
    """Provide a block with no insertion opportunities."""
    return make_empty_block_tree()


# ===== Test Cases =====


class TestDeadCodeInsertionRule:
    """Comprehensive tests for dead code insertion behavior."""

    # ===== Core Behavior =====

    def test_initialization(self):
        """Ensure the rule initializes with correct defaults."""
        rule = DeadCodeInsertionRule()

        assert rule.rule_name == "dead-code-insertion"

    def test_apply_with_none_root(self, mutation_context):
        """Ensure apply handles None safely."""
        rule = DeadCodeInsertionRule()

        assert rule.apply(None, mutation_context) == []  # type: ignore

    def test_requires_language(self, mutation_context):
        """Root without language should raise an error."""
        root = Node((0, 0), (0, 0), "module", children=[])

        rule = DeadCodeInsertionRule()

        with pytest.raises(ValueError, match="No language found"):
            rule.apply(root, mutation_context)

    # ===== Basic Mutation =====

    def test_inserts_dead_code(self, simple_block_tree, mutation_context):
        """Ensure dead code is inserted into a valid block."""
        rule = DeadCodeInsertionRule(level=3, seed=1)

        records = rule.apply(simple_block_tree, mutation_context)

        assert len(records) >= 1

        dead_nodes = [node for node in simple_block_tree.traverse() if node.type == "dead_code"]

        assert len(dead_nodes) >= 1

    def test_returns_valid_mutation_records(self, simple_block_tree, mutation_context):
        """Ensure mutation records contain correct metadata."""
        rule = DeadCodeInsertionRule(level=3, seed=1)

        records = rule.apply(simple_block_tree, mutation_context)

        assert len(records) >= 1

        for record in records:
            assert record.metadata["node_type"] == "dead_code"
            assert record.metadata["new_val"] is not None
            assert record.metadata["insertion_point"] is not None

    # ===== Determinism =====

    def test_is_deterministic(self):
        """Same seed should produce identical insertions and positions."""
        rule1 = DeadCodeInsertionRule(level=3, seed=42)
        rule2 = DeadCodeInsertionRule(level=3, seed=42)

        tree1 = make_simple_block_tree()
        tree2 = make_simple_block_tree()

        ctx1 = MutationContext()
        ctx2 = MutationContext()

        records1 = rule1.apply(tree1, ctx1)
        records2 = rule2.apply(tree2, ctx2)

        assert len(records1) == len(records2)

        assert [(r.metadata["new_val"], r.metadata["insertion_point"]) for r in records1] == [
            (r.metadata["new_val"], r.metadata["insertion_point"]) for r in records2
        ]

    # ===== Fallback Behavior =====

    def test_guarantees_at_least_one_insertion(self, simple_block_tree, mutation_context):
        """At low probability, fallback should still ensure one insertion."""
        rule = DeadCodeInsertionRule(level=0, seed=999)

        records = rule.apply(simple_block_tree, mutation_context)

        assert len(records) >= 1

    def test_no_candidates_produces_no_insertions(self, empty_block_tree, mutation_context):
        """If no valid insertion points exist, no mutations should occur."""
        rule = DeadCodeInsertionRule(level=3, seed=1)

        records = rule.apply(empty_block_tree, mutation_context)

        assert records == []

    # ===== Structural Correctness =====

    def test_inserts_before_target_node(self, simple_block_tree, mutation_context):
        """Dead code should be inserted before the original statement."""
        rule = DeadCodeInsertionRule(level=3, seed=1)

        root = simple_block_tree
        block = next(node for node in root.traverse() if node.semantic_label == "block_scope")

        original_child = block.children[0]

        rule.apply(root, mutation_context)

        assert block.children[0].type == "dead_code"
        assert block.children[1] == original_child

    def test_inserted_node_has_parent(self, simple_block_tree, mutation_context):
        """Inserted nodes should maintain correct parent references."""
        rule = DeadCodeInsertionRule(level=3, seed=1)

        rule.apply(simple_block_tree, mutation_context)

        for node in simple_block_tree.traverse():
            if node.type == "dead_code":
                assert node.parent is not None
