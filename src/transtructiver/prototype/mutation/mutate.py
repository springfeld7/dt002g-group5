"""Main module for demonstrating mutation of a Concrete Syntax Tree (CST).

This module provides a simple entry point that loads a mock CST, applies
mutation rules (specifically identifier renaming), and displays the results.

Usage:
    python -m prototype.mutation.mutate
"""

from ..parsing.parser import Parser
from .rules.identifier_renaming.rename_identifiers import RenameIdentifiersRule
from .mutation_engine import MutationEngine


def main():
    """Main function that demonstrates CST mutation.

    This function:
    1. Loads a mock CST (a simple function definition)
    2. Prints the original tree structure
    3. Creates a MutationEngine with RenameIdentifiersRule
    4. Applies the mutation rules to transform the tree
    5. Prints the mutated tree structure
    """
    lang = "cpp"
    code = """add(a, b) {
    return a + b;
}
"""
    parser = Parser()
    cst, discard_reason = parser.parse(code, lang)

    if cst:
        print("Before mutation:")
        cst.pretty()

        engine = MutationEngine([RenameIdentifiersRule()])
        engine.apply_mutations(cst)

        print("\nAfter mutation:")
        cst.pretty()


if __name__ == "__main__":
    main()
