"""Unit tests for the RenameIdentifiersRule mutation rule."""

import pytest
from transtructiver.mutation.rules.identifier_renaming.rename_identifiers import (
    RenameIdentifiersRule,
)
from transtructiver.node import Node
from transtructiver.mutation.rules.mutation_rule import MutationRecord
from transtructiver.mutation.mutation_types import MutationAction


# ===== Helpers =====


def _wire_parents(node: Node, parent: Node | None = None) -> Node:
    """Recursively populate parent links after literal tree construction."""
    node.parent = parent
    for child in node.children:
        _wire_parents(child, node)
    return node


def label_nodes(root: Node) -> Node:
    """Annotate semantic labels and fields from CST structure only."""
    _wire_parents(root)
    root.semantic_label = "root"
    if not getattr(root, "language", None):
        if root.type == "module":
            root.language = "python"
        elif root.type == "program":
            root.language = "java"

    # Phase 1: scope/type nodes.
    for node in root.traverse():
        if node.type == "function_definition":
            node.semantic_label = "function_scope"
        elif node.type == "block":
            node.semantic_label = "block_scope"

    # Phase 2: identifier and typed nodes.
    for node in root.traverse():
        if node.type == "type":
            node.field = "type"

        if node.type != "identifier" or node.parent is None:
            continue

        parent = node.parent

        # Function declaration names.
        if parent.type == "function_definition" and parent.children and parent.children[0] is node:
            node.semantic_label = "function_name"
            node.field = "name"
            continue

        # Parameter declarations.
        if parent.type == "typed_parameter" and parent.children and parent.children[0] is node:
            node.semantic_label = "parameter_name"
            node.field = "name"
            continue

        # Type identifiers.
        if parent.type in {"type", "type_identifier"}:
            node.semantic_label = "type_name"
            continue

        # Assignment declarations.
        if parent.type == "assignment" and parent.children and parent.children[0] is node:
            node.semantic_label = "variable_name"
            node.field = "left"
            continue

        # Shallow identifier usages in common test scopes.
        if parent.type in {"module", "program", "block"}:
            node.semantic_label = "variable_name"

    return root


def make_sample_tree() -> Node:
    """Create a small module tree with repeated variable identifiers."""
    root = Node(
        (0, 0),
        (0, 10),
        "module",
        children=[
            Node((1, 0), (1, 1), "identifier", text="x"),
            Node((1, 2), (1, 3), "identifier", text="y"),
            Node((1, 4), (1, 5), "identifier", text="x"),
            Node((1, 6), (1, 7), "number", text="1"),
        ],
    )

    return label_nodes(root)


def make_unannotated_identifier_tree() -> tuple[Node, Node]:
    """Create a module tree with one identifier and no semantic label."""
    ident = Node((1, 0), (1, 1), "identifier", text="x")
    root = Node((0, 0), (0, 10), "module", children=[ident])
    label_nodes(root)
    ident.semantic_label = None
    return root, ident


def make_module_function_tree() -> tuple[Node, Node]:
    """Create a module tree with one function-name identifier: foo."""
    function_name = Node((1, 4), (1, 7), "identifier", text="foo")
    root = Node(
        (0, 0),
        (0, 10),
        "module",
        children=[Node((1, 0), (1, 10), "function_definition", children=[function_name])],
    )
    return label_nodes(root), function_name


def make_program_function_tree() -> tuple[Node, Node]:
    """Create a program tree with one function-name identifier: foo."""
    function_name = Node((1, 4), (1, 7), "identifier", text="foo")
    root = Node(
        (0, 0),
        (0, 10),
        "program",
        children=[Node((1, 0), (1, 10), "function_definition", children=[function_name])],
    )
    return label_nodes(root), function_name


def make_variable_parameter_tree() -> tuple[Node, Node, Node]:
    """Create a module tree with one variable x and one parameter p."""
    variable_id = Node((1, 0), (1, 1), "identifier", text="x")
    parameter_id = Node((2, 5), (2, 6), "identifier", text="p")
    root = Node(
        (0, 0),
        (0, 10),
        "module",
        children=[
            Node((1, 0), (1, 10), "assignment", children=[variable_id]),
            Node(
                (2, 0),
                (2, 10),
                "function_definition",
                children=[
                    Node(
                        (2, 4),
                        (2, 10),
                        "parameters",
                        children=[
                            Node(
                                (2, 4),
                                (2, 10),
                                "typed_parameter",
                                children=[parameter_id],
                            )
                        ],
                    )
                ],
            ),
        ],
    )
    return label_nodes(root), variable_id, parameter_id


def make_variable_only_tree() -> tuple[Node, Node]:
    """Create a module tree with one variable declaration: data."""
    variable_id = Node((1, 0), (1, 4), "identifier", text="data")
    root = Node(
        (0, 0),
        (0, 10),
        "module",
        children=[Node((1, 0), (1, 10), "assignment", children=[variable_id])],
    )
    return label_nodes(root), variable_id


def make_program_bar_function_tree() -> tuple[Node, Node]:
    """Create a program tree with one function-name identifier: bar."""
    function_name = Node((1, 4), (1, 7), "identifier", text="bar")
    root = Node(
        (0, 0),
        (0, 10),
        "program",
        children=[Node((1, 0), (1, 10), "function_definition", children=[function_name])],
    )
    return label_nodes(root), function_name


def make_scoped_tree_with_shadowing() -> Node:
    """Create a scope tree where inner and outer declarations share a name."""
    root = Node(
        (0, 0),
        (0, 0),
        "module",
        children=[
            Node(
                (1, 0),
                (1, 5),
                "assignment",
                children=[Node((1, 0), (1, 1), "identifier", text="x")],
            ),
            Node(
                (2, 0),
                (5, 0),
                "function_definition",
                children=[
                    Node((2, 4), (2, 7), "identifier", text="foo"),
                    Node(
                        (3, 0),
                        (5, 0),
                        "block",
                        children=[
                            Node(
                                (3, 4),
                                (3, 9),
                                "assignment",
                                children=[Node((3, 4), (3, 5), "identifier", text="x")],
                            ),
                            Node((4, 4), (4, 5), "identifier", text="x"),
                        ],
                    ),
                ],
            ),
            Node((6, 0), (6, 1), "identifier", text="x"),
        ],
    )

    return label_nodes(root)


def make_typed_parameter_tree() -> tuple[Node, Node]:
    """Create a typed-parameter function tree and return parameter identifier."""
    parameter_id = Node((1, 5), (1, 9), "identifier", text="items")

    root = Node(
        (0, 0),
        (0, 10),
        "module",
        children=[
            Node(
                (1, 0),
                (1, 10),
                "function_definition",
                children=[
                    Node(
                        (1, 4),
                        (1, 10),
                        "parameters",
                        children=[
                            Node(
                                (1, 5),
                                (1, 10),
                                "typed_parameter",
                                children=[
                                    parameter_id,
                                    Node(
                                        (1, 11),
                                        (1, 15),
                                        "type",
                                        children=[
                                            Node((1, 11), (1, 15), "identifier", text="list")
                                        ],
                                    ),
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )

    return label_nodes(root), parameter_id


def make_assignment_type_tree() -> tuple[Node, Node, Node]:
    """Create assignment-based declaration tree used for suffix inference tests."""
    values_id = Node((1, 0), (1, 6), "identifier", text="values")

    message_id = Node((2, 0), (2, 7), "identifier", text="message")

    root = Node(
        (0, 0),
        (0, 10),
        "module",
        children=[
            Node(
                (1, 0),
                (1, 10),
                "assignment",
                children=[
                    values_id,
                    Node((1, 7), (1, 8), "operator", text="="),
                    Node((1, 9), (1, 11), "list", children=[]),
                ],
            ),
            Node(
                (2, 0),
                (2, 12),
                "assignment",
                children=[
                    message_id,
                    Node((2, 8), (2, 9), "operator", text="="),
                    Node((2, 10), (2, 17), "string", text='"hello"'),
                ],
            ),
        ],
    )

    return label_nodes(root), values_id, message_id


# ===== Fixtures =====


@pytest.fixture
def sample_tree():
    """Create a sample node tree with identifiers for testing.

    Returns a root node with 4 children:
    - [0]: identifier "x"
    - [1]: identifier "y"
    - [2]: identifier "x"
    - [3]: number "1"
    """
    return make_sample_tree()


@pytest.fixture
def unannotated_identifier_tree() -> tuple[Node, Node]:
    """Tree with one unlabeled identifier node."""
    return make_unannotated_identifier_tree()


@pytest.fixture
def module_function_tree() -> tuple[Node, Node]:
    """Module root with a single function-name identifier."""
    return make_module_function_tree()


@pytest.fixture
def program_function_tree() -> tuple[Node, Node]:
    """Program root with a single function-name identifier."""
    return make_program_function_tree()


@pytest.fixture
def variable_parameter_tree() -> tuple[Node, Node, Node]:
    """Module root with one variable and one parameter identifier."""
    return make_variable_parameter_tree()


@pytest.fixture
def variable_only_tree() -> tuple[Node, Node]:
    """Module root with one variable identifier."""
    return make_variable_only_tree()


@pytest.fixture
def program_bar_function_tree() -> tuple[Node, Node]:
    """Program root with a function identifier named bar."""
    return make_program_bar_function_tree()


@pytest.fixture
def scoped_tree_with_shadowing() -> Node:
    """Create tree where inner scope declares the same identifier as outer scope."""
    return make_scoped_tree_with_shadowing()


@pytest.fixture
def typed_parameter_tree() -> tuple[Node, Node]:
    """Function tree with one typed parameter and its identifier node."""
    return make_typed_parameter_tree()


@pytest.fixture
def assignment_type_tree() -> tuple[Node, Node, Node]:
    """Module tree with typed assignment declarations and identifier nodes."""
    return make_assignment_type_tree()


# ===== Test Cases =====


class TestRenameIdentifierCoreBehavior:
    """Core initialization, mutation, and state-reset behavior."""

    def test_rename_identifier_rule_initialization(self):
        """Ensure the subclass initializes base and custom fields correctly."""
        rule = RenameIdentifiersRule()

        assert rule.name == "RenameIdentifiersRule"

    def test_rename_identifier_rule_apply_with_none_root(self):
        """Ensure apply handles None root safely."""
        rule = RenameIdentifiersRule()

        assert rule.apply(None) == []  # type: ignore

    def test_rename_identifier_rule_mutates_node_text(self, sample_tree):
        """Ensure apply renames identifier node text values consistently."""
        first_x, first_y, second_x, non_identifier = sample_tree.children

        rule = RenameIdentifiersRule()
        rule.apply(sample_tree)

        assert first_x.text != "x"
        assert first_y.text != "y"
        assert second_x.text != "x"

        assert non_identifier.text == "1"
        assert second_x.text == first_x.text

    def test_rename_identifier_rule_returns_mutation_records(self, sample_tree):
        """Ensure apply returns correct mutation records for renamed identifiers."""
        first_x, first_y, second_x, _ = sample_tree.children

        rule = RenameIdentifiersRule()
        records = rule.apply(sample_tree)

        assert len(records) == 3
        assert all(record.action == MutationAction.RENAME for record in records)
        assert records[0].node_id == (1, 0)

        assert records[0].metadata != {"new_val": "x"}
        assert records[0].metadata == {"new_val": first_x.text}

        assert records[1].metadata != {"new_val": "y"}
        assert records[1].metadata == {"new_val": first_y.text}

        assert records[2].metadata == {"new_val": second_x.text}
        assert records[2].metadata == {"new_val": first_x.text}


class TestRenameIdentifierScopeBehavior:
    """Scope handling and shadowing behavior."""

    def test_rename_identifier_rule_uses_scope_stack_for_shadowing(
        self, scoped_tree_with_shadowing: Node
    ):
        """Inner declaration of same name should not reuse outer scope rename."""
        rule = RenameIdentifiersRule()
        records: list[MutationRecord] = rule.apply(scoped_tree_with_shadowing)

        renamed_x_nodes: list[Node] = [
            node
            for node in scoped_tree_with_shadowing.traverse()
            if node.type == "identifier" and node.start_point in {(1, 0), (3, 4), (4, 4), (6, 0)}
        ]
        renamed_values: dict[tuple[int, int], str | None] = {
            node.start_point: node.text for node in renamed_x_nodes
        }

        assert len(records) == 4
        # Outer x and outer use should be equal
        assert renamed_values[(1, 0)] == renamed_values[(6, 0)]
        # Inner x and inner use should be equal
        assert renamed_values[(3, 4)] == renamed_values[(4, 4)]
        # Outer x and inner x should not be equal
        assert renamed_values[(1, 0)] != renamed_values[(3, 4)]

    def test_rename_identifier_rule_clears_scope_state_between_runs(self, sample_tree):
        """Internal scope stack should be reset after apply finishes."""
        rule = RenameIdentifiersRule()
        rule.apply(sample_tree)

        assert rule.scope == []


class TestRenameIdentifierTargeting:
    """Target selection and configuration validation behavior."""

    def test_rename_identifier_rule_skips_unannotated_identifiers(
        self, unannotated_identifier_tree
    ):
        """Identifiers without semantic labels should not be renamed."""
        root, ident = unannotated_identifier_tree

        rule = RenameIdentifiersRule()
        records = rule.apply(root)

        assert records == []
        assert ident.text == "x"

    def test_rename_identifier_rule_skips_non_variable_annotations(self, module_function_tree):
        """Only variable-like semantic labels should be renamed by default."""
        root, function_name = module_function_tree

        rule = RenameIdentifiersRule()
        records = rule.apply(root)

        assert records == []
        assert function_name.text == "foo"

    def test_rename_identifier_rule_can_target_function_names_by_keyword(
        self, module_function_tree
    ):
        """Keyword-based targeting should allow function_name renames."""
        root, function_name = module_function_tree

        rule = RenameIdentifiersRule(targets=["function"])
        records = rule.apply(root)

        assert len(records) == 1
        assert function_name.text == "foo_fn"

    def test_rename_identifier_rule_can_target_only_parameter_names(self, variable_parameter_tree):
        """Target keywords should restrict renaming to selected semantic labels."""
        root, variable_id, parameter_id = variable_parameter_tree

        rule = RenameIdentifiersRule(targets=["parameter"])
        records = rule.apply(root)

        assert len(records) == 1
        assert variable_id.text == "x"
        assert parameter_id.text == "pp"

    def test_rename_identifier_rule_rejects_unknown_target_keyword(self):
        """Unknown keyword should raise a clear configuration error."""
        with pytest.raises(ValueError, match="Unsupported rename target keyword"):
            RenameIdentifiersRule(targets=["not_a_real_target"])


class TestRenameIdentifierSuffixInference:
    """Type/suffix inference behavior for declarations."""

    def test_rename_identifier_rule_uses_parameter_type_for_suffix(self, typed_parameter_tree):
        """Typed parameters should receive a type-aware suffix when possible."""
        root, parameter_id = typed_parameter_tree

        rule = RenameIdentifiersRule(targets=["parameter"])
        records = rule.apply(root)

        assert len(records) == 1
        assert parameter_id.text == "items_list"

    def test_rename_identifier_rule_uses_assignment_value_type_for_suffix(
        self, assignment_type_tree
    ):
        """Assignment declarations should infer suffixes from assigned values."""
        root, values_id, message_id = assignment_type_tree

        rule = RenameIdentifiersRule(targets=["variable"])
        records = rule.apply(root)

        assert len(records) == 2
        assert values_id.text == "valuess"
        assert message_id.text == "messagee"


class TestRenameIdentifierFormatting:
    """Language-specific formatting and fallback behavior."""

    def test_rename_identifier_rule_uses_java_style_for_program_root(self, program_function_tree):
        """Program roots should use non-Python naming style formatting."""
        root, function_name = program_function_tree

        rule = RenameIdentifiersRule(targets=["function"])
        records = rule.apply(root)

        assert len(records) == 1
        assert function_name.text == "fooFn"

    def test_rename_identifier_rule_formats_python_and_java_differently(self):
        """Suffix formatting should differ between module and program roots."""
        python_root, python_function = make_module_function_tree()
        java_root, java_function = make_program_function_tree()

        python_rule = RenameIdentifiersRule(targets=["function"])
        java_rule = RenameIdentifiersRule(targets=["function"])
        python_rule.apply(python_root)
        java_rule.apply(java_root)

        assert python_function.text == "foo_fn"
        assert java_function.text == "fooFn"

    def test_rename_identifier_rule_empty_suffix_fallback_is_stable(self, variable_only_tree):
        """When no suffix can be inferred, renaming should use fallback behavior."""
        root, variable_id = variable_only_tree

        rule = RenameIdentifiersRule(targets=["variable"])
        records = rule.apply(root)

        assert len(records) == 1
        assert variable_id.text == "dataa"

    def test_rename_identifier_rule_overwrites_language_each_apply_run(
        self, program_bar_function_tree
    ):
        """Language chosen per root should not leak between consecutive apply calls."""
        python_root, python_function = make_module_function_tree()
        java_root, java_function = program_bar_function_tree

        rule = RenameIdentifiersRule(targets=["function"])
        rule.apply(python_root)
        rule.apply(java_root)

        assert python_function.text == "foo_fn"
        assert java_function.text == "barFn"
