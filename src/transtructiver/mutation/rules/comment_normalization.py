"""comment_normalization.py

A concrete MutationRule that normalizes comment content by replacing it with
a fixed placeholder while preserving comment delimiters.

This module defines CommentNormalizationRule, which traverses a CST to identify
comment nodes based on semantic labels, and updates their text content to a standardized format.

Each modification generates a MutationRecord capturing the original coordinates
and content of the comment for downstream verification and manifest generation.
"""

from typing import List

from transtructiver.mutation.mutation_context import MutationContext
from .mutation_rule import MutationRule, MutationRecord
from ...node import Node


COMMENT_CONFIG = {
    "line_comment": ["//", "#", "--"],
    "block_comment": [("/*", "*/"), ('"""', '"""'), ("'''", "'''")],
}


class CommentNormalizationRule(MutationRule):
    """Normalizes comments by replacing content with a uniform dot-block.
    Example: // Comment -> //........
    Example: /* comment */ -> /*........*/
    """

    # CLI rule name (used by the auto-discovery in cli.py).
    rule_name = "comment-normalization"

    FILLER = "........"

    def apply(self, root: Node, context: MutationContext) -> List[MutationRecord]:
        """Apply the CommentNormalization mutation rule to the CST.

        This method recursively traverses the tree rooted at `root`,
        identifies comment nodes based on semantic labels,
        and updates their text to a normalized format while preserving delimiters.

        Each modification generates a MutationRecord with the original coordinates
        and content of the comment.

        Args:
            root (Node): The root node of the CST to mutate.
            context (MutationContext): The context object for tracking mutation state,
                                       not used in this rule but included for interface consistency.

        Returns:
            List[MutationRecord]: A list of all modifications performed,
                each containing the original coordinates and content of the normalized comment.
        """
        records: List[MutationRecord] = []

        for child in list(root.children):
            delimiters = COMMENT_CONFIG.get(child.semantic_label)

            if delimiters:
                # Handle nested block comments (needed for Python triple-quoted docstrings)
                if child.children:
                    for sub in child.children:
                        if sub.type == "string_content":
                            records.append(self._update_text(sub, self.FILLER))

                # Handle leaf node comments (line comments or block comments without nested content)
                else:
                    new_text = self._format(child.text, delimiters)
                    records.append(self._update_text(child, new_text))

            # Recurse through the tree
            records.extend(self.apply(child, context))

        return records

    def _format(self, text: str, delimiters: list) -> str:
        """Replaces text with the FILLER constant while preserving comment delimiters.

        This method checks the provided text against known comment delimiters and
        returns a new string that maintains the original delimiters but replaces the content
        with a fixed placeholder. It handles both line and block comment styles.

        Args:
            text (str): The original comment text to be normalized.
            delimiters (list): A list of delimiters to check against,
                which can include line commentprefixes or block comment start/end pairs.
        Returns:
            str: The normalized comment text with original delimiters and content replaced by FILLER.
        """
        stripped_text = text.strip()
        for d in delimiters:

            if isinstance(d, tuple):  # Block Style
                start, end = d
                if stripped_text.startswith(start) and stripped_text.endswith(end):
                    return f"{start}{self.FILLER}{end}"

            else:  # Line Style
                if stripped_text.startswith(d):
                    return f"{d}{self.FILLER}"

        return text

    def _update_text(self, node: Node, new_text: str) -> MutationRecord:
        """Updates the text of a node and returns a MutationRecord describing the change.

        This method modifies the node's text to the new value and creates a MutationRecord
        that captures the original coordinates and content of the node before the update.

        Args:
            node (Node): The node to update.
            new_text (str): The new text to set on the node.
        Returns:
            MutationRecord: A record of the mutation performed,
            including the node's original coordinates and content.
        """
        return self.record_reformat(node, new_text)
