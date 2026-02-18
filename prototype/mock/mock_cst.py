"""Mock Concrete Syntax Tree (CST) for testing and demonstration.

This module provides a sample CST representing a simple function definition.
It's used for testing mutation rules and the mutation engine.

The sample CST represents the following pseudocode:
    add(a, b) { return a + b; }
"""

from ..node import Node

cst = Node("function_definition", [
    Node("identifier", text="add"),
    Node("parameters", [
        Node("identifier", text="a"),
        Node("identifier", text="b")
    ]),
    Node("body", [
        Node("return_statement", [
            Node("binary_expression", [
                Node("identifier", text="a"),
                Node("operator", text="+"),
                Node("identifier", text="b")
            ])
        ])
    ])
])
