"""Mutation Context Module

Provides the MutationContext class to manage shared state, such as 
synthetic coordinate generation, across multiple mutation rules.
"""

from dataclasses import dataclass


@dataclass
class MutationContext:
    """Shared state for a single mutation lifecycle."""

    synthetic_row_counter: int = -1

    def next_id(self) -> int:
        """
        Returns the next unique synthetic ID and decrements the counter.
        Used to ensure no two rules inject nodes with colliding coordinates.
        """
        current = self.synthetic_row_counter
        self.synthetic_row_counter -= 1
        return current
