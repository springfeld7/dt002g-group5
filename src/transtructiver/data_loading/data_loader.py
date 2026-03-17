"""
data_loader.py

Unified DataLoader abstraction and ParquetDataLoader implementation for snippet streaming and checkpointing.

This module defines:
    - DataLoader: a factory function that returns the appropriate loader based on file extension.
    - AbstractDataLoader: an extensible base class for all snippet loaders.
    - ParquetDataLoader: a concrete loader for .parquet files using pyarrow.

The DataLoader interface hides file format details from the CLI and pipeline logic.
To add support for new formats, implement a subclass of AbstractDataLoader and update the factory.
Checkpoints are managed per loader instance, supporting resumable processing.
"""

import os
import json
from typing import Iterator, Optional, Any
from abc import ABC, abstractmethod
import pyarrow.parquet as pq


def DataLoader(filepath: str, checkpoint_path: str | None = None):
    """
    Factory function for snippet data loaders.

    Args:
        filepath: Path to the dataset file (.parquet or other supported formats).
        checkpoint_path: Optional path for checkpoint file.

    Returns:
        An instance of AbstractDataLoader (concrete subclass).

    Raises:
        NotImplementedError: If the file extension is unsupported.

    Extension:
        To support new formats, add a new loader subclass and update this dispatch logic.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".parquet":
        return ParquetDataLoader(filepath, checkpoint_path=checkpoint_path)
    raise NotImplementedError(f"No DataLoader implemented for file extension: {ext}")


class AbstractDataLoader(ABC):
    """
    Abstract base class for snippet data loaders.

    Subclasses must implement iter_snippets().
    Provides checkpoint management for resumable processing.

    Args:
        filepath: Path to the dataset file.
        checkpoint_path: Optional path for checkpoint file.

    Usage:
        Use DataLoader factory to obtain a loader instance.
    """

    def __init__(self, filepath: str, checkpoint_path: Optional[str] = None):
        self.filepath = filepath
        self.checkpoint_path = checkpoint_path or "output/checkpoint.json"

    @abstractmethod
    def iter_snippets(self, batch_size: int, start_index: int) -> Iterator[tuple[int, str, str]]:
        """Yield (global_index, code, language) for each snippet."""
        pass

    def load_checkpoint(self, resume: bool) -> int:
        """Load checkpoint and return the next index to process.

        Args:
            resume (bool): Whether to resume from checkpoint.

        Returns:
            int: Next index to process.
        """
        if not resume or not os.path.exists(self.checkpoint_path):
            return 0
        with open(self.checkpoint_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return int(payload.get("next_index", 0))

    def save_checkpoint(self, next_index: int, stats: Any) -> None:
        """Persist a resumable checkpoint atomically.

        Args:
            next_index (int): Next index to process.
            stats (RunStats): Run statistics to save.
        """
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        tmp_path = self.checkpoint_path + ".tmp"
        payload = {
            "next_index": next_index,
            "parsed_ok": getattr(stats, "parsed_ok", 0),
            "parse_skipped": getattr(stats, "parse_skipped", 0),
            "verified_ok": getattr(stats, "verified_ok", 0),
            "verified_fail": getattr(stats, "verified_fail", 0),
        }
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        os.replace(tmp_path, self.checkpoint_path)


class ParquetDataLoader(AbstractDataLoader):
    """
    Data loader for reading code snippets from a Parquet file using pyarrow.

    Implements iter_snippets() for efficient batch streaming.
    """

    def iter_snippets(self, batch_size: int, start_index: int) -> Iterator[tuple[int, str, str]]:
        """Stream snippets from parquet in bounded-size batches.

        Args:
            batch_size (int): Number of rows per batch.
            start_index (int): Index to start streaming from.

        Returns:
            Iterator[tuple[int, str, str]]: Yields (global_index, code, language).
        """
        parquet_file = pq.ParquetFile(self.filepath)
        global_index = 0
        for batch in parquet_file.iter_batches(batch_size=batch_size, columns=["code", "language"]):
            batch_dict = batch.to_pydict()
            codes = batch_dict.get("code", [])
            languages = batch_dict.get("language", [])
            for code, language in zip(codes, languages):
                if global_index >= start_index:
                    yield global_index, code, language
                global_index += 1
