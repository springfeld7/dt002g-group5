"""Data Loader for reading code snippets from Parquet files.

The DataLoader handles loading a Parquet file into a Pandas DataFrame
and provides methods to inspect or print the loaded data.
"""

from typing import Optional
import pandas as pd


class DataLoader:
    """Engine for loading and managing code snippets from a Parquet file.

    The DataLoader encapsulates reading a Parquet file into a Pandas DataFrame
    and provides utility methods for inspecting and printing the loaded data.

    Attributes:
        file_path (str): Path to the Parquet file.
        df (pd.DataFrame): The loaded DataFrame (None until load() is called).
    """

    def __init__(self, file_path: str) -> None:
        """Initialize the DataLoader with the path to the Parquet file.

        Args:
            file_path (str): Path to the Parquet file to load.
        """
        self.file_path: str = file_path
        self.df: Optional[pd.DataFrame] = None

    def load(self) -> pd.DataFrame:
        """Load the Parquet file into a Pandas DataFrame.

        Returns:
            pd.DataFrame: The loaded DataFrame containing code snippets.
        """
        try:
            self.df = pd.read_parquet(self.file_path, engine="pyarrow")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Parquet file not found: {self.file_path}") from e
        except ValueError as e:
            raise ValueError(f"Failed to read Parquet file: {self.file_path}") from e

        print(f"Loaded {len(self.df)} rows from {self.file_path}")
        return self.df

    def print_entries(self) -> None:
        """Print all rows in the loaded DataFrame in a readable format.

        Raises:
            ValueError: If the DataFrame has not been loaded yet.

        Example:
            >>> loader = DataLoader("sample.parquet")
            >>> loader.load()
            >>> loader.print_entries()
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load() first.")

        print("DataFrame shape:", self.df.shape)
        print()
        for idx, row in self.df.iterrows():  # Print each row with index, code, and language
            print(f"Row {idx}:")
            print(f"  index      : {row['index']}")
            print(f"  code       : {row['code']}")
            print(f"  language   : {row['language']}")
            print()

    def __repr__(self) -> str:
        """Return a string representation of the DataLoader instance.

        Shows the file path and the number of rows currently loaded (0 if not loaded).

        Returns:
            str: A readable representation of the DataLoader instance.
        """
        return (
            f"DataLoader(file_path='{self.file_path}', "
            f"rows_loaded={len(self.df) if self.df is not None else 0})"
        )
