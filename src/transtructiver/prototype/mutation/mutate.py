"""Main module for demonstrating mutation of a Concrete Syntax Tree (CST).

This module provides a simple entry point that loads a mock CST, applies
mutation rules (specifically identifier renaming), and displays the results.

Usage:
    python -m prototype.mutation.mutate
"""

from ..mock.mock_cst import cst
from .mutation_rule import RenameIdentifiersRule
from .mutation_engine import MutationEngine


def main():
    """Main function that demonstrates CST mutation.
    
    This function:
    1. Loads a mock CST (a simple function definition)
    2. Prints the original tree structure
    3. Creates a MutationEngine with RenameIdentifiersRule
    4. Applies the mutation rules to transform the tree
    5. Prints the mutated tree structure
    
    The mutation rule prefixes all identifiers with "x_", so:
    - 'add' becomes 'x_add'
    - 'a' becomes 'x_a'
    - 'b' becomes 'x_b'
    """
    print("Before mutation:")
    cst.pretty()

    engine = MutationEngine([RenameIdentifiersRule()])
    mutated = engine.applyMutations(cst)

    print("\nAfter mutation:")
    mutated.pretty()

if __name__ == '__main__':
    main()
