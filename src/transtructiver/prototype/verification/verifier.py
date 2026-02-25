"""
Structural Isomorphism Verifier (SIV) Module.

This module provides the SIVerifier class, which audits code mutations 
by comparing the Concrete Syntax Tree (CST) of original and mutated code 
against a structural manifest. It performs a strict coordinate-based 
validation, returning a binary result (1.0 for a successful match, 
0.0 for any structural or content mismatch).
"""

import csv
import os


class SIVerifier:
    """Auditor that verifies structural isomorphism between two trees."""

    def __init__(self):
        self.errors = []
        self.renamed_paths = {}
        self.ignored_paths = []
        self.success_count = 0


    def verify(self, orig_node, mut_node, snippet_manifest) -> bool:
        """
        Public entry point for the verification process.
        Returns True only if the score is exactly 1.0.
        """
        self.errors = []
        self.success_count = 0
        self.renamed_paths = snippet_manifest.get("renamed_paths", {})
        self.ignored_paths = snippet_manifest.get("ignored_paths", [])

        self._verify_recursive(orig_node, mut_node, "0")

        return len(self.errors) == 0


    def _verify_recursive(self, orig, mut, path) -> bool:
        """Private recursive worker that walks the tree structure."""
        if path in self.ignored_paths:
            return True

        self._verify_node_integrity(orig, mut, path)

        if len(orig.children) != len(mut.children):
            self.errors.append(f"STRUCTURAL_MISMATCH at {path}: Child count differs")
            return False

        for i, (orig_child, mut_child) in enumerate(zip(orig.children, mut.children)):
            self._verify_recursive(orig_child, mut_child, f"{path}.{i}")

        return len(self.errors) == 0


    def _verify_node_integrity(self, orig, mut, path) -> bool:
        """Checks if types match and validates renamed identifiers."""
        if orig.type != mut.type:
            self.errors.append(f"TYPE_MISMATCH at {path}: {orig.type} vs {mut.type}")
            return False

        if path in self.renamed_paths:
            expected_text = self.renamed_paths[path]
            if mut.text != expected_text:
                self.errors.append(f"MUTATION_FAIL at {path}: Expected {expected_text}, got {mut.text}")
        else:
            if orig.text != mut.text:
                self.errors.append(f"UNEXPECTED_CHANGE at {path}: {orig.text} -> {mut.text}")
        
        return len(self.errors) == 0


    def write_summary(self, snippet_id, verified):
        """Appends the verification result to a headerless CSV."""
        score = 1.0 if verified else 0.0
        reason = "N/A" if verified else (self.errors[0] if self.errors else "Mismatch")

        with open('summary_log.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([snippet_id, score, reason])
