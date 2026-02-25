"""Command-line interface for the TranStructIVer pipeline.

This module provides the entry point for running the complete transformation
pipeline on datasets, including data loading, parsing, mutation, and verification.
"""

import argparse
import json
import os
from .data_load.data_loader import DataLoader
from .parsing.parser import Parser
from .mutation.mutation_engine import MutationEngine
from .mutation.mutation_rule import RenameIdentifiersRule
from .verification.verifier import SIVerifier


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

    verifier = SIVerifier()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(base_dir, "manifest.json")
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        print(f"Loaded manifest from: {manifest_path}")
    except FileNotFoundError:
        print(f"Error: Manifest NOT found at {manifest_path}")
        return

    for idx, row in df.iterrows():
        code = row["code"]
        language = row["language"]
        snippet_id = f"row_{idx}"
        snippet_manifest = manifest.get(snippet_id, {})

        print(f"\n[{snippet_id}] Parsing...")
        orig_cst = parser.parse(code, language)
        print("Original tree:")
        orig_cst.pretty()

        mut_cst = engine.applyMutations(orig_cst.clone())
        print("\nMutated code:")
        mut_cst.pretty()

        verified = verifier.verify(orig_cst, mut_cst, snippet_manifest)
        verifier.write_summary(snippet_id, verified)

        print(f'\nRow {idx}: {"PASS" if verified else "FAIL"}')


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
