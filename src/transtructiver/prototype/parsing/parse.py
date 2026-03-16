"""Entry point for parsing demo.

Runs the parser on a small example and prints the resulting CST as a
pretty-printed Node tree.
"""

from collections import deque

from ..node import Node
from .parser import Parser


INTERESTING_IDENTIFIERS = [
    "variable_declarator/java",
    "declaration/cpp",
    "assignment_expression/cpp",
]


def main():
    """Run a simple parsing demo and print the CST."""
    parser = Parser()

    # Test examples for different languages
    test_cases = [
        (
            "Python",
            """def add(a, b):
	return a + b
""",
            "python",
        ),
        (
            "Java",
            """add(a, b) {
    return a + b;
}
""",
            "java",
        ),
        (
            "C++",
            """add(a, b) {
    return a + b;
}
""",
            "cpp",
        ),
    ]

    # Test the first one (change index to test others)
    test_index = 1
    language_name, code, language = test_cases[test_index]

    print(f"=" * 60)
    print(f"Testing {language_name} Parser")
    print(f"=" * 60)
    print(f"\nSource code:\n{code}\n")
    print(f"=" * 60)

    cst, discard_reason = parser.parse(code, language)

    if cst is not None:
        print("Parsed CST:")
        cst.pretty()

        print("\n\n=== SEMANTIC ANNOTATIONS ===\n")

        annotated_nodes = []

        for node in cst.traverse():
            if hasattr(node, "semantic_label") and node.semantic_label is not None:
                annotated_nodes.append(node)

        if annotated_nodes:
            print(f"Found {len(annotated_nodes)} annotated nodes:\n")
            for node in annotated_nodes:
                parent_type = node.parent.type if node.parent else "None"
                print(
                    f"  [{node.semantic_label}] '{node.text}' (type: {node.type}, parent: {parent_type})"
                )
        else:
            print("No semantic annotations found.")

        print("\n=== ALL IDENTIFIERS ===\n")
        identifiers = [node for node in cst.traverse() if node.type == "identifier"]
        print(f"Found {len(identifiers)} identifiers:\n")
        for node in identifiers[:20]:  # Limit to first 20
            parent_type = node.parent.type if node.parent else "None"
            label = (
                f"[{node.semantic_label}]"
                if hasattr(node, "semantic_label") and node.semantic_label
                else "[unlabeled]"
            )
            print(f"  {label} '{node.text}' (parent: {parent_type})")

    else:
        print(f"Invalid snippet, reason to discard: {discard_reason}")

    print(f"\n{'='*60}")
    print(f"To test other languages, change test_index in main():")
    print(f"  0 = Python, 1 = Java, 2 = C++")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
