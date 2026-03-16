"""Command-line interface for the TranStructIVer pipeline.

This module provides the entry point for running the complete transformation
pipeline on datasets, including data loading, parsing, mutation, and verification.

Outputs written per run (inside ``--output-dir``):
    * ``manifest.jsonl``       — FR-5: one JSON-Lines record per snippet
    * ``augmented_dataset.parquet`` — FR-9: original/mutated code pairs
    * ``summary_log.csv``      — FR-10: semantics-preservation pass/fail log
"""

import argparse
import json
import os
from dataclasses import dataclass
from typing import Iterator
import pyarrow.parquet as pq
from .parsing.parser import Parser
from .mutation.mutation_engine import MutationEngine
from .mutation.rules.identifier_renaming.rename_identifiers import RenameIdentifiersRule
from .node import Node
from .reporting import summary_logger
from .reporting.output_manager import OutputManager, RunStats
from .verification.si_verifier import SIVerifier


RULE_REGISTRY = {"rename-identifier": RenameIdentifiersRule}

# PROTOTYPE-ONLY OUTPUT:
# Keep developer-facing logs enabled in prototype runs.
# For production hardening, set this to False (or remove related helpers/calls).
PROTOTYPE_OUTPUT_ENABLED = True


@dataclass
class RenameRuleOptions:
    """CLI options for RenameIdentifiersRule construction."""

    level: int = 0
    targets: list[str] | None = None


@dataclass
class PipelineOptions:
    """Runtime options for large-scale dataset processing."""

    batch_size: int = 1000
    checkpoint_every: int = 1000
    checkpoint_path: str = "output/checkpoint.json"
    resume: bool = False
    max_rows_per_shard: int = 0
    compress_output: bool = False


def _prototype_log(message: str) -> None:
    """PROTOTYPE-ONLY: central log sink for easy production removal."""
    if PROTOTYPE_OUTPUT_ENABLED:
        print(message)


def _prototype_pretty(label: str, root: Node) -> None:
    """PROTOTYPE-ONLY: pretty-print a CST for debugging and demos."""
    if PROTOTYPE_OUTPUT_ENABLED:
        print(label)
        print(root.to_code())


def _iter_snippets(
    filepath: str,
    batch_size: int,
    start_index: int,
) -> Iterator[tuple[int, str, str]]:
    """Stream snippets from parquet in bounded-size batches."""
    parquet_file = pq.ParquetFile(filepath)
    global_index = 0

    for batch in parquet_file.iter_batches(batch_size=batch_size, columns=["code", "language"]):
        batch_dict = batch.to_pydict()
        codes = batch_dict.get("code", [])
        languages = batch_dict.get("language", [])
        for code, language in zip(codes, languages):
            if global_index >= start_index:
                yield global_index, code, language
            global_index += 1


def _load_checkpoint(checkpoint_path: str, resume: bool) -> int:
    """Load checkpoint and return the next index to process."""
    if not resume or not os.path.exists(checkpoint_path):
        return 0

    with open(checkpoint_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return int(payload.get("next_index", 0))


def _save_checkpoint(checkpoint_path: str, next_index: int, stats: RunStats) -> None:
    """Persist a resumable checkpoint atomically."""
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    tmp_path = checkpoint_path + ".tmp"
    payload = {
        "next_index": next_index,
        "parsed_ok": stats.parsed_ok,
        "parse_skipped": stats.parse_skipped,
        "verified_ok": stats.verified_ok,
        "verified_fail": stats.verified_fail,
    }
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    os.replace(tmp_path, checkpoint_path)


def _validate_rules(rules: list[str]) -> list[str]:
    """Return unsupported rule names so callers can fail fast and explicitly."""
    return [rule for rule in rules if rule not in RULE_REGISTRY]


def _build_engine(rules: list[str], rename_options: RenameRuleOptions) -> MutationEngine:
    """Construct a mutation engine with per-rule configuration."""
    configured_rules = []
    for rule_name in rules:
        if rule_name == "rename-identifier":
            configured_rules.append(
                RenameIdentifiersRule(
                    level=rename_options.level,
                    targets=rename_options.targets,
                )
            )
            continue

        configured_rules.append(RULE_REGISTRY[rule_name]())

    return MutationEngine(configured_rules)


def run_pipeline(
    filepath: str,
    rules: list[str],
    output_dir: str = "output",
    rename_options: RenameRuleOptions | None = None,
    pipeline_options: PipelineOptions | None = None,
):
    """Run the complete TranStructIVer pipeline on a dataset file.

    For each snippet the pipeline:
    1. Parses the original code into a CST.
    2. Clones the CST and applies mutation rules.
    3. Writes the transformation manifest (FR-5).
    4. Writes the original/mutated code pair to the augmented dataset (FR-9).
    5. Verifies semantic preservation and logs the result (FR-10).

    Args:
        filepath (str): Path to the dataset file (Parquet format).
        rules (list[str]): Mutation rule names to apply (see RULE_REGISTRY).
        output_dir (str): Directory for all output files. Created if absent.
        rename_options (RenameRuleOptions | None): Options for rename-identifier
            rule configuration (level and target restrictions).
        pipeline_options (PipelineOptions | None): Performance options for
            streaming, sharding, compression, and checkpointing.

    Raises:
        ValueError: If any rule name is not registered in RULE_REGISTRY.
    """
    os.makedirs(output_dir, exist_ok=True)
    pipeline_options = pipeline_options or PipelineOptions()
    start_index = _load_checkpoint(pipeline_options.checkpoint_path, pipeline_options.resume)

    parser = Parser()

    unsupported_rules = _validate_rules(rules)
    if unsupported_rules:
        raise ValueError(f"Arguments contain unsupported mutation rule: {unsupported_rules}")

    rename_options = rename_options or RenameRuleOptions()
    engine = _build_engine(rules, rename_options)
    verifier = SIVerifier()
    stats = RunStats()
    processed_since_checkpoint = 0

    with OutputManager(
        output_dir,
        max_rows_per_shard=pipeline_options.max_rows_per_shard,
        compress_output=pipeline_options.compress_output,
    ) as outputs:
        for idx, code, language in _iter_snippets(
            filepath,
            batch_size=pipeline_options.batch_size,
            start_index=start_index,
        ):
            snippet_id = f"row_{idx}"

            _prototype_log(f"\n[{snippet_id}] Parsing...")
            orig_cst, parse_err = parser.parse(code, language)
            if orig_cst is None:
                stats.parse_skipped += 1
                _prototype_log(f"  Skipped ({parse_err})")
                processed_since_checkpoint += 1
                if (
                    pipeline_options.checkpoint_every > 0
                    and processed_since_checkpoint >= pipeline_options.checkpoint_every
                ):
                    _save_checkpoint(pipeline_options.checkpoint_path, idx + 1, stats)
                    processed_since_checkpoint = 0
                continue

            stats.parsed_ok += 1
            _prototype_pretty("Original tree:", orig_cst)

            # Clone before mutation so we keep the clean original for comparison
            mut_cst = orig_cst.clone()
            engine.apply_mutations(mut_cst)

            _prototype_pretty("\nMutated code:", mut_cst)

            # Write manifest for this snippet
            outputs.write_manifest(idx, snippet_id, engine.manifest.to_dict())

            # Write original/mutated code pair
            original_code = orig_cst.to_code()
            mutated_code = mut_cst.to_code()
            outputs.write_dataset_row(idx, snippet_id, original_code, mutated_code)

            # Verify semantic preservation and append to summary log
            verified = verifier.verify(orig_cst, mut_cst, engine.manifest)
            if verified:
                stats.verified_ok += 1
            else:
                stats.verified_fail += 1

            summary_logger.write_summary(
                snippet_id=snippet_id,
                verified=verified,
                errors=verifier.errors,
                writer=outputs.summary_writer,
            )

            _prototype_log(f'\nRow {idx}: {"PASS" if verified else "FAIL"}')
            processed_since_checkpoint += 1

            if (
                pipeline_options.checkpoint_every > 0
                and processed_since_checkpoint >= pipeline_options.checkpoint_every
            ):
                _save_checkpoint(pipeline_options.checkpoint_path, idx + 1, stats)
                processed_since_checkpoint = 0

        if processed_since_checkpoint > 0:
            _save_checkpoint(pipeline_options.checkpoint_path, idx + 1, stats)

        summary_logger.write_summary_totals(
            parsed_ok=stats.parsed_ok,
            parse_skipped=stats.parse_skipped,
            verified_ok=stats.verified_ok,
            verified_fail=stats.verified_fail,
            writer=outputs.summary_writer,
        )

        manifest_path, dataset_path, summary_path = outputs.output_paths_summary()

    _prototype_log(f"\nManifest written to:        {manifest_path}")
    _prototype_log(f"Augmented dataset written to: {dataset_path}")
    _prototype_log(f"Summary log written to:       {summary_path}")
    _prototype_log(
        "Summary metrics: "
        f"processed={stats.processed}, "
        f"parse_skipped={stats.parse_skipped}, "
        f"success_rate={stats.success_rate:.2%}"
    )


def main():
    """Main entry point for the TranStructIVer CLI.

    Command-line Arguments:
        filepath: Path to the dataset file (Parquet format) to process.
        --rules: Mutation rules to apply (default: rename-identifier).
        --output-dir: Directory for output files (default: output).

    Example:
        uv run proto-cli src\\transtructiver\\prototype\\data_load\\sample.parquet
        uv run proto-cli dataset.parquet --rules rename-identifier --output-dir results
    """
    argparser = argparse.ArgumentParser(
        prog="TranStructIVer", description="Run the TranStructIVer pipeline on a dataset file."
    )
    argparser.add_argument("filepath", help="Path to the dataset file")
    argparser.add_argument("rules", nargs="*", help="Mutation rules", default=["rename-identifier"])
    argparser.add_argument(
        "--output-dir", default="output", help="Directory for output files (default: output)"
    )
    argparser.add_argument(
        "--rename-level",
        type=int,
        default=0,
        help="RenameIdentifiersRule level (default: 0)",
    )
    argparser.add_argument(
        "--rename-targets",
        nargs="+",
        choices=["variable", "parameter", "property", "function", "class"],
        default=None,
        help=(
            "Restrict rename-identifier to selected target kinds. "
            "Examples: --rename-targets variable parameter"
        ),
    )
    argparser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Parquet streaming batch size (default: 1000)",
    )
    argparser.add_argument(
        "--resume",
        action="store_true",
        help="Resume processing from checkpoint if checkpoint file exists.",
    )
    argparser.add_argument(
        "--checkpoint-path",
        default=None,
        help="Checkpoint path (default: <output-dir>/checkpoint.json)",
    )
    argparser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1000,
        help="Write checkpoint every N processed snippets (default: 1000)",
    )
    argparser.add_argument(
        "--max-rows-per-shard",
        type=int,
        default=0,
        help="Shard manifest/dataset outputs every N rows (0 disables sharding).",
    )
    argparser.add_argument(
        "--compress-output",
        action="store_true",
        help="Compress output files using gzip.",
    )
    args = argparser.parse_args()

    rename_options = RenameRuleOptions(
        level=args.rename_level,
        targets=args.rename_targets,
    )

    checkpoint_path = args.checkpoint_path
    if checkpoint_path is None:
        checkpoint_path = os.path.join(args.output_dir, "checkpoint.json")

    pipeline_options = PipelineOptions(
        batch_size=args.batch_size,
        checkpoint_every=args.checkpoint_every,
        checkpoint_path=checkpoint_path,
        resume=args.resume,
        max_rows_per_shard=args.max_rows_per_shard,
        compress_output=args.compress_output,
    )

    run_pipeline(args.filepath, args.rules, args.output_dir, rename_options, pipeline_options)


if __name__ == "__main__":
    main()
