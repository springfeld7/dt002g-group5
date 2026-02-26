"""
Unit tests for the DataLoader class.

This module tests the main functionality of DataLoader, including:
- Successful loading of a valid Parquet file.
- Handling of missing files (FileNotFoundError).
- Handling of invalid files (ValueError).

Temporary Parquet files are created for testing purposes using the tempfile module.
"""

import os
import unittest
from tempfile import TemporaryDirectory

import pandas as pd

from transtructiver.data_loading.data_loader import DataLoader


class TestDataLoader(unittest.TestCase):
    """Unit tests for the DataLoader class."""

    def setUp(self):
        """Create a temporary Parquet file for testing."""
        self.temp_dir = TemporaryDirectory()
        self.file_path = os.path.join(self.temp_dir.name, "test.parquet")

        # Create a simple DataFrame to write
        self.df = pd.DataFrame(
            {
                "index": [0, 1],
                "code": ["print('hello')", "x = 1 + 1"],
                "language": ["python", "python"],
            }
        )
        self.df.to_parquet(self.file_path, engine="pyarrow")

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_load_successful(self):
        """Test that a valid Parquet file loads correctly and matches the original DataFrame."""
        loader = DataLoader(self.file_path)
        df_loaded = loader.load()

        pd.testing.assert_frame_equal(
            df_loaded, self.df
        )  # Check that loaded DataFrame matches original
        self.assertEqual(len(loader.df), 2)  # Check that the number of rows loaded is correct

    def test_load_missing_file(self):
        """Test that loading a non-existent file raises FileNotFoundError."""
        missing_path = os.path.join(self.temp_dir.name, "missing.parquet")

        loader = DataLoader(missing_path)

        with self.assertRaises(FileNotFoundError):
            loader.load()

    def test_load_invalid_file(self):
        """Test that loading an invalid file raises a proper error."""
        invalid_parquet = os.path.join(self.temp_dir.name, "invalid.parquet")
        with open(invalid_parquet, "w") as f:
            f.write("not a parquet file")

        loader = DataLoader(invalid_parquet)

        with self.assertRaises(ValueError):
            loader.load()


if __name__ == "__main__":
    unittest.main()
