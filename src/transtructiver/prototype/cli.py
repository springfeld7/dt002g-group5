"""Command-line interface for the TranStructIVer pipeline.

This module provides the entry point for running the complete transformation
pipeline on datasets, including data loading, parsing, mutation, and verification.
"""

import argparse
from .data_load.data_loader import DataLoader
from .parsing.parser import Parser
from .mutation.mutation_engine import MutationEngine
from .mutation.mutation_rule import RenameIdentifiersRule

# from '.verification.verifier' import 'verifier'


RULE_REGISTRY = {"rename-identifier": RenameIdentifiersRule}


def run_pipeline(filepath: str, rules: list[str]):
    """Run the complete TranStructIVer pipeline on a dataset file.

    This function orchestrates the full transformation pipeline:
    1. Load code samples from a dataset file
    2. Parse each code sample into a CST
    3. Apply mutation rules to transform the CST
    4. Display the mutated code

    Args:
        filepath (str): Path to the dataset file (Parquet format) containing code samples.
            Expected columns: 'code' (source code) and 'language' (programming language).
        rules (list[str]): List of mutation rule names to apply. Available rules are
            defined in RULE_REGISTRY. Example: ['rename-identifier', 'other-rule'].

    Raises:
        ValueError: If any of the specified rules are not found in RULE_REGISTRY.

    Example:
        >>> run_pipeline('dataset.parquet', ['rename-identifier'])
    """
    data_loader = DataLoader(filepath)
    df = data_loader.load()
    data_loader.print_entries()

    parser = Parser()

    unsupported_rules = []
    for rule in rules:
        if not rule in RULE_REGISTRY:
            unsupported_rules.append(rule)

    if len(unsupported_rules) > 0:
        raise ValueError(f"Arguments contain unsupported mutation rule: {unsupported_rules}")

    engine = MutationEngine([RULE_REGISTRY[name]() for name in rules])

    for idx, row in df.iterrows():
        code = row["code"]
        language = row["language"]

        print("Parsing...")
        cst = parser.parse(code, language)
        print("Original tree:")
        cst.pretty()

        print("\nMutated code:")
        engine.applyMutations(cst).pretty()

        # 4. Verify
        # verified = verify(cst, mutated)

        print(f"\nRow {idx}: OK")


def main():
    """Main entry point for the TranStructIVer CLI.

    Parses command-line arguments and executes the transformation pipeline.

    Command-line Arguments:
        filepath: Path to the dataset file (Parquet format) to process.
        rules: Optional list of mutation rules to apply. Defaults to ['rename-identifier'].

    Example:
        python -m prototype.cli dataset.parquet rename-identifier
        development: uv run proto-cli src\\transtructiver\\prototype\\data_load\\sample.parquet
    """
    argparser = argparse.ArgumentParser(
        prog="TranStructIVer", description="Run the TranStructIVer pipeline on a dataset file."
    )
    argparser.add_argument("filepath", help="Path to the dataset file")
    argparser.add_argument("rules", nargs="*", help="Mutation rules", default=["rename-identifier"])
    args = argparser.parse_args()

    run_pipeline(args.filepath, args.rules)


if __name__ == "__main__":
    main()
