"""Entry point for parsing demo.

Runs the parser on a small example and prints the resulting CST.
"""

from .parser import Parser


def main():
    """Run a simple parsing demo and print the CST."""
    parser = Parser()
    cst = parser.parse("def add(a, b): return a + b")

    print("Parsed CST:")
    cst.pretty()


if __name__ == '__main__':
    main()
