"""Data Loader for reading code snippets from Parquet files.

The DataLoader handles loading a Parquet file into a Pandas DataFrame
and provides simple methods to inspect or print the loaded data.
"""

import pandas as pd
import os

class DataLoader:
    """Engine for loading and managing code snippets from a Parquet file.

    The DataLoader encapsulates reading a Parquet file into a Pandas DataFrame
    and provides utility methods for inspecting and printing the loaded data.

    Attributes:
        file_path (str): Path to the Parquet file.
        df (pd.DataFrame): The loaded DataFrame (None until load() is called).
    """

    def __init__(self, file_path: str):
        """Initialize the DataLoader with the path to the Parquet file.

        Args:
            file_path (str): Path to the Parquet file to load.
        """
        self.file_path = file_path
        self.df = None

    def load(self) -> pd.DataFrame:
        """Load the Parquet file into a Pandas DataFrame.

        Returns:
            pd.DataFrame: The loaded DataFrame containing code snippets.
        """
        self.df = pd.read_parquet(self.file_path, engine="pyarrow")
        print(f"Loaded {len(self.df)} rows from {self.file_path}")
        return self.df

    def print_entries(self):
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
        for idx, row in self.df.iterrows():
            print(f"Row {idx}:")
            print(f"  index      : {row['index']}")
            print(f"  code       : {row['code']}")
            print(f"  language   : {row['language']}")
            print()

    def __repr__(self):
        """Return a string representation of the DataLoader for debugging.

        Shows the file path and the number of rows currently loaded (0 if not loaded).

        Returns:
            str: A human-readable representation of the DataLoader instance.
        """
        return (f"DataLoader(file_path='{self.file_path}', "
            f"rows_loaded={len(self.df) if self.df is not None else 0})")

if __name__ == "__main__":
    """
    Test the DataLoader by loading the sample Parquet file
    and printing its contents.
    """
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, "sample.parquet")

    loader = DataLoader(file_path)
    loader.load()
    loader.print_entries()
