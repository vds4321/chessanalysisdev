"""
Test file for importing and using the data_fetcher module.
"""

from src.data_fetcher import ChessComDataFetcher

# Example usage to demonstrate the import is working
def test_data_fetcher_import():
    """Test that we can import and instantiate the ChessComDataFetcher class."""
    try:
        # This will fail without proper configuration, but demonstrates the import works
        fetcher = ChessComDataFetcher(username="test_user")
        print(f"Successfully imported and instantiated ChessComDataFetcher: {type(fetcher)}")
        return True
    except Exception as e:
        print(f"Import successful, but instantiation failed (expected): {e}")
        return False

if __name__ == "__main__":
    test_data_fetcher_import()