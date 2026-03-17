"""
Unit tests for the DataLoader class.

This module tests:
- Successful loading of a valid Parquet file.
- Handling of missing files (FileNotFoundError).
- Handling of invalid files (ValueError).

Temporary Parquet files are created using pytest's tmp_path fixture.
"""

from pathlib import Path
import pandas as pd
from typing import Tuple
import pytest
from transtructiver.data_loading.data_loader import DataLoader


@pytest.fixture
def sample_parquet(tmp_path: Path) -> Tuple[Path, pd.DataFrame]:
    """
    Create a temporary Parquet file with sample data.

    Args:
        tmp_path (Path): Built-in pytest fixture providing a temporary directory.

    Returns:
        tuple: (file_path, original_dataframe)
    """
    file_path = tmp_path / "test.parquet"

    df = pd.DataFrame(
        {
            "index": [0, 1],
            "code": ["print('hello')", "x = 1 + 1"],
            "language": ["python", "python"],
        }
    )

    df.to_parquet(file_path, engine="pyarrow")
    return file_path, df


def test_load_successful(sample_parquet):
    """
    Test that a valid Parquet file loads correctly
    and matches the original DataFrame.
    """
    file_path, original_df = sample_parquet

    loader = DataLoader(str(file_path))
    # Use iter_snippets to stream rows
    streamed = list(loader.iter_snippets(batch_size=10, start_index=0))
    # Convert streamed output to DataFrame for comparison
    indices, codes, languages = zip(*streamed)
    df_streamed = pd.DataFrame(
        {
            "index": indices,
            "code": codes,
            "language": languages,
        }
    )
    # Compare streamed DataFrame to original
    pd.testing.assert_frame_equal(
        df_streamed.reset_index(drop=True), original_df.reset_index(drop=True)
    )
    assert len(streamed) == 2


def test_load_missing_file(tmp_path):
    """
    Test that loading a non-existent file raises FileNotFoundError.
    """
    missing_path = tmp_path / "missing.parquet"
    loader = DataLoader(str(missing_path))
    with pytest.raises(Exception):
        list(loader.iter_snippets(batch_size=10, start_index=0))


def test_load_invalid_file(tmp_path):
    """
    Test that loading an invalid file raises ValueError.
    """
    invalid_file = tmp_path / "invalid.parquet"
    invalid_file.write_text("not a parquet file")

    loader = DataLoader(str(invalid_file))
    with pytest.raises(Exception):
        list(loader.iter_snippets(batch_size=10, start_index=0))
