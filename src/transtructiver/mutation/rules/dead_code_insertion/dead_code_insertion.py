"""Rule for injecting language-specific dead code into a CST.

This module defines the InsertDeadCodeRule, which traverses a CST and identifies
safe containers (blocks, functions, etc.) for injecting unreachable code. It 
leverages language-specific lexicons to ensure the injected code is syntactically 
valid and uses a ScopeManager to prevent identifier collisions.
"""

import random
from typing import List

from ....node import Node
from ..mutation_rule import MutationRule, MutationRecord
from ...mutation_context import MutationContext
from .lexicons.dead_code_lexicon import DeadCodeLexicon
from .lexicons.registry import get_lexicon
from .insertion_strategies.registry import get_strategy
from .insertion_strategies.insertion_strategy import InsertionStrategy
from ..utils.scope_manager import ScopeManager


class DeadCodeInsertionRule(MutationRule):
    """
    Injects unreachable code blocks with scope-aware identifier generation.

    The rule uses a probability-based approach governed by the 'level' attribute
    to decide where to insert code. It ensures that at least one insertion occurs
    if the tree contains valid container nodes.

    Attributes:
        rule_name (str): CLI identifier for the rule.
        _NATURAL_VAR_NAMES (List[str]): A pool of human-like variable names for injections.
        _LOOP_VAR_NAMES (List[str]): Common loop variable names for generating loop constructs.
        _SCOPE_LABELS (Set[str]): Semantic labels that denote new scopes for identifier tracking.
        _level (int): Intensity level for insertion frequency (0-3).
        _rng (random.Random): Internal RNG for deterministic behavior based on seed.
        _base_indent (str): The string used for indentation in injected code (e.g. "    " for 4 spaces).
        _scope (ScopeManager): Manages variable scopes to avoid naming collisions during injection.
    """

    rule_name = "dead-code-insertion"

    # The level probability of insertion is calculated as follows:
    # Level 0: 1 * (0.5 / 4) = 0.125 (12.5% chance)
    # Level 1: 2 * (0.5 / 4) = 0.25 (25% chance)
    # Level 2: 3 * (0.5 / 4) = 0.375 (37.5% chance)
    # Level 3: 4 * (0.5 / 4) = 0.5 (50% chance)
    _LEVEL_PROBABILITY = 0.5 / 4

    # A pool of natural variable names to choose from for injected code, enhancing plausibility.
    _NATURAL_VAR_NAMES = [
        "val",
        "temp",
        "result",
        "data",
        "item",
        "entry",
        "element",
        "content",
        "obj",
        "target",
        "source",
        "output",
        "input",
        "buffer",
        "cache",
        "count",
        "total",
        "sum",
        "min",
        "max",
        "avg",
        "offset",
        "index",
        "pos",
        "limit",
        "threshold",
        "delta",
        "factor",
        "scale",
        "ratio",
        "size",
        "length",
    ]

    # Standard loop indices
    _LOOP_VAR_NAMES = [
        "i",
        "j",
        "k",
        "l",
        "m",
        "n",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "w",
        "x",
        "y",
        "z",
    ]

    # Semantic labels that introduce a fresh naming scope during traversal.
    _SCOPE_LABELS = {
        "root",
        "function_scope",
        "class_scope",
        "block_scope",
        "loop_scope",
    }

    # Valid parent labels/types for block scopes where dead code can be safely injected.
    _VALID_PARENT_LABELS = {
        "loop_scope",
        "function_scope",
    }
    _VALID_PARENT_TYPES = {"if_statement", "else_clause", "for_statement", "while_statement"}

    def __init__(self, level: int = 0, seed: int = 42, indent_unit: str = None) -> None:
        """
        Initializes the rule with configuration for intensity and determinism.

        Args:
            level (int): Intensity level (0-3). 0 is sparse (~10% chance),
                3 is dense (~40% chance).
            seed (int): Seed for the internal random number generator.
            indent_unit (str): The string used for indentation in injected code,
                               if None, it will be auto-detected from the CST or default to 4 spaces.
        """
        super().__init__()
        self._level = level
        self._rng = random.Random(seed)
        self._base_indent = indent_unit
        self._scope = ScopeManager()

    def _detect_indent_unit(self, root: Node) -> str:
        """
        Scans the tree for the first whitespace node that starts at column 0
        and has a length greater than 0.

        This method is used to auto-detect the indentation unit, fallbacks to 4 spaces if none is found.

        Args:
            root (Node): The root of the CST to scan for indentation patterns.

        Returns:
            str: The detected indentation unit (e.g. "    " for 4 spaces) or a default if none found.
        """
        # Traverse to find the first 'indentation' whitespace with a length > 0
        for node in root.traverse():
            if node.type == "whitespace" and node.start_point[1] == 0:
                if node.text:
                    return node.text
        return "    "  # Fallback to 4 spaces if no indentation pattern is detected

    def apply(self, root: Node, context: MutationContext) -> List[MutationRecord]:
        """
        Entry point for the mutation. Validates language and initializes
        traversal.

        Args:
            root (Node): The annotated CST root node.
            context (MutationContext): The mutation context for tracking state across rules.

        Returns:
            List[MutationRecord]: A list of insertion records performed.

        Raises:
            ValueError: If the root node lacks language metadata.
        """
        if root is None:
            return []

        # Determine language
        language = root.language.lower().strip() if root.language else None
        if not language:
            raise ValueError("No language found on root node.")
        # Retrieve the lexicon class for the specified language
        lexicon_cls = get_lexicon(language)
        lexicon = lexicon_cls(self._rng)

        # Retrieve the insertion strategy for the specified language
        insertion_strategy = get_strategy(language)

        # Determine indentation
        indent = self._base_indent or self._detect_indent_unit(root)
        lexicon.set_indent_unit(indent)

        return self._apply_traversal(root, context, insertion_strategy, lexicon)

    def _apply_traversal(
        self,
        root: Node,
        context: MutationContext,
        strategy: InsertionStrategy,
        lexicon: DeadCodeLexicon,
    ) -> List[MutationRecord]:
        """
        Iteratively walks the tree to track scopes, record identifiers,
        and perform safe code injections using language-specific strategies.

        Args:
            root (Node): The CST root node.
            context (MutationContext): Tracking state across rules.
            lexicon (DeadCodeLexicon): Generator for the code strings.
            strategy (InsertionStrategy): Structural rules for the language.

        Returns:
            List[MutationRecord]: Records of all code insertions performed.
        """
        self._scope.reset()
        records: List[MutationRecord] = []
        candidates: List[tuple[Node, str]] = []
        insertion_probability = (self._level + 1) * self._LEVEL_PROBABILITY

        # Iterative stack: (node, is_exit_marker)
        stack: List[tuple[Node, bool]] = [(root, False)]

        while stack:
            node, is_exit = stack.pop()

            # Scope exit handling
            if is_exit:
                self._scope.exit_scope()
                continue

            # Scope entry handling
            if node.semantic_label in self._SCOPE_LABELS:
                self._scope.enter_scope()
                stack.append((node, True))

            # Identifier Tracking (to avoid shadowing/clashes)
            if "identifier" in node.type and node.text:
                self._scope.declare(node.text, "exists")

            if self._is_valid_container(node):
                self._scan_and_inject(
                    node, strategy, lexicon, context, insertion_probability, candidates, records
                )

            # Push children in reverse for DFS order
            for child in reversed(node.children):
                stack.append((child, False))

        # Guarantee one insertion if we found candidates but didn't hit the random chance
        if not records and candidates:
            self._ensure_minimum_mutation(candidates, records, lexicon, context)

        self._scope.reset()
        return records

    def _scan_and_inject(
        self,
        node: Node,
        strategy: InsertionStrategy,
        lexicon: DeadCodeLexicon,
        context: MutationContext,
        prob: float,
        candidates: List[tuple[Node, str]],
        records: List[MutationRecord],
    ) -> None:
        """
        Processes a block's children for potential code injection.

        Args:
            node (Node): The block node whose children are being scanned.
            strategy (InsertionStrategy): The language-specific insertion strategy.
            lexicon (DeadCodeLexicon): The lexicon for generating dead code snippets.
            context (MutationContext): The mutation context for tracking state across rules.
            prob (float): The probability of performing an insertion at each valid gap.
            candidates (List[tuple[Node, str]]): A list to collect valid insertion points for fallback.
            records (List[MutationRecord]): A list to collect MutationRecords of performed insertions.
        """
        prefix = strategy.get_indent_prefix(node)
        if prefix is None:
            return

        preceding = None
        for child in list(node.children):
            if strategy.is_valid_gap(child, preceding):
                candidates.append((child, prefix))
                if self._rng.random() < prob:
                    records.append(self._inject_dead_code(child, prefix, lexicon, context))

            if strategy.is_terminal(child):
                break
            preceding = child

    def _inject_dead_code(
        self, target: Node, prefix: str, lexicon: DeadCodeLexicon, context: MutationContext
    ) -> MutationRecord:
        """
        Creates a synthetic node and records the insertion.

        Args:
            target (Node): The node before which the dead code will be inserted.
            prefix (str): The indentation prefix for the generated code.
            lexicon (DeadCodeLexicon): The lexicon to generate the dead code string.
            context (MutationContext): The mutation context for tracking state across rules.

        Returns:
            MutationRecord: The record of the insertion performed.
        """
        var_name = self._get_var_name("d")
        loop_var = self._get_loop_var()
        dead_code = lexicon.get_random_dead_code(prefix, var_name, loop_var)

        # Create an adopt dead code node
        dc_node = Node(
            start_point=(context.next_id(), -1),
            end_point=target.start_point,
            type="dead_code",
            text=dead_code,
        )
        dc_node.parent = target.parent

        # Insert into the tree
        idx = target.parent.children.index(target)
        target.parent.children.insert(idx, dc_node)

        return self.record_insert(
            dc_node.start_point,
            insertion_point=target.start_point,
            new_text=dead_code,
            new_type="dead_code",
        )

    def _is_valid_container(self, node: Node) -> bool:
        """
        Checks if the node is a block that lives inside a function, loop, or conditional.

        Args:
            node (Node): The node to check for eligibility as a container for dead code insertion.

        Returns:
            bool: True if the node is a valid container for insertion, False otherwise.
        """
        if node.semantic_label != "block_scope":
            return False

        parent = node.parent
        if not parent:
            return False

        return (
            parent.semantic_label in self._VALID_PARENT_LABELS
            or parent.type in self._VALID_PARENT_TYPES
        )

    def _get_var_name(self, prefix: str) -> str:
        """
        Generates a unique name by checking the natural pool first, then falling
        back to a hex-suffixed name.

        Args:
            prefix (str): A base prefix for the variable name.

        Returns:
            str: A unique variable name that does not collide with existing identifiers in scope.
        """
        # Attempt to use a name from the natural pool first,
        # ensuring it doesn't collide with existing identifiers in scope
        for candidate in self._NATURAL_VAR_NAMES:
            if self._scope.resolve(candidate) is None:
                self._scope.declare(candidate, "injected")
                return candidate

        # Fallback if all natural names are taken in the current scope
        return self._generate_fallback_name(prefix)

    def _generate_fallback_name(self, prefix: str) -> str:
        """
        Generates a unique hex-suffixed variable name that does not collide
        with existing identifiers in the current scope.

        Args:
            prefix (str): Base string for the variable name.

        Returns:
            str: Unique variable name.
        """
        while True:
            candidate = f"{prefix}_{self._rng.getrandbits(16):x}"
            if self._scope.resolve(candidate) is None:
                self._scope.declare(candidate, "injected")
                return candidate

    def _get_loop_var(self) -> str:
        """
        Attempts to find a unique standard loop index (i, j, k, etc.).

        Returns:
            str: A human-like loop variable or a unique fallback if all are taken.
        """
        for candidate in self._LOOP_VAR_NAMES:
            if self._scope.resolve(candidate) is None:
                self._scope.declare(candidate, "injected")
                return candidate
        return self._get_var_name("idx")

    def _ensure_minimum_mutation(
        self,
        candidates: List[tuple[Node, str]],
        records: List[MutationRecord],
        lexicon: DeadCodeLexicon,
        context: MutationContext,
    ) -> None:
        """
        Performs a single guaranteed injection from the available candidates.

        Args:
            candidates (List[tuple[Node, str]]): A list of valid insertion points collected during traversal.
            records (List[MutationRecord]): The list of MutationRecords to append to if an insertion is performed.
            lexicon (DeadCodeLexicon): The lexicon to generate the dead code string.
            context (MutationContext): The context for the mutation.
        """
        child, prefix = self._rng.choice(candidates)
        records.append(self._inject_dead_code(child, prefix, lexicon, context))
