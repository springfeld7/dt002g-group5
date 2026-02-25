"""Mock Mutated Concrete Syntax Tree (CST) for testing the verification prototype.

This module provides a manually mutated version of a simple function definition CST,
simulating the output of a mutation engine. It is intended for use in the
Structural Isomorphism Verification (SIV) prototype to test verification logic
independently of the parser and mutation engine.

The original function represented (before mutation) was:
    add(a, b) { return a + b; }

The mutations applied in this mock CST include:
    - Renaming the function identifier: add → x_add
    - Renaming parameter identifiers: a → x_a, b → x_b
    - Updating the corresponding identifiers in the return statement to match
"""

from ..node import Node

cst = Node("function_definition", [
    Node("identifier", text="x_add"),
    Node("parameters", [
        Node("identifier", text="x_a"),
        Node("identifier", text="x_b")
    ]),
    Node("body", [
        Node("return_statement", [
            Node("binary_expression", [
                Node("identifier", text="x_a"),
                Node("operator", text="+"),
                Node("identifier", text="x_b")
            ])
        ])
    ])
])
