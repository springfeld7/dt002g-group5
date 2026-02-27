"""Entry point for parsing demo.

Runs the parser on a small example and prints the resulting CST as a
pretty-printed Node tree.
"""

from .parser import Parser


def main():
    """Run a simple parsing demo and print the CST."""
    parser = Parser()
    cst, discard_reason = parser.parse("void f() { return; } void f() { int x = 0; }", "cpp")

    if cst is not None:
        print("Parsed CST:")
        cst.pretty()
    else:
        print(f"Invalid snippet, reason to discard: {discard_reason}")


if __name__ == "__main__":
    main()
