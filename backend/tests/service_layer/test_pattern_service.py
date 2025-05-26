import pytest
from pathlib import Path
from unittest.mock import mock_open, MagicMock
from app.service_layer.pattern_service import PatternService, PatternNotFoundError
# import builtins # No longer needed for mocking open

def test_load_pattern(mocker):
    # Setup mock directory and file paths
    mock_patterns_dir = MagicMock(spec=Path)
    pattern_service = PatternService(mock_patterns_dir)

    mock_file_path = MagicMock(spec=Path)
    mock_patterns_dir.__truediv__.return_value = mock_file_path # patterns_dir / "file.md"

    # Test Case 1: Pattern found and read from file
    mock_file_path.exists.return_value = True
    mock_file_path.open = mock_open(read_data='mocked content') # Use as context manager

    content = pattern_service.get_pattern_content("test_pattern")
    assert content == 'mocked content'
    mock_patterns_dir.__truediv__.assert_called_once_with("test_pattern.md")
    mock_file_path.exists.assert_called_once()
    mock_file_path.open.assert_called_once_with('r', encoding='utf-8')

    # Test Case 2: Pattern found in cache
    # Reset mocks for the next call if necessary, or ensure they behave as expected
    # For cache hit, 'exists' and 'open' should not be called again for "test_pattern"
    mock_file_path.exists.reset_mock()
    mock_file_path.open.reset_mock()

    content_cached = pattern_service.get_pattern_content("test_pattern")
    assert content_cached == 'mocked content'
    mock_file_path.exists.assert_not_called()
    mock_file_path.open.assert_not_called()

    # Test Case 3: Pattern not found
    mock_non_existent_file_path = MagicMock(spec=Path)
    # Configure __truediv__ to return this new mock for a different pattern name
    mock_patterns_dir.__truediv__.reset_mock() # Reset previous return_value or side_effect
    mock_patterns_dir.__truediv__.return_value = mock_non_existent_file_path
    mock_non_existent_file_path.exists.return_value = False

    with pytest.raises(PatternNotFoundError):
        pattern_service.get_pattern_content("non_existent_pattern")
    mock_patterns_dir.__truediv__.assert_called_once_with("non_existent_pattern.md")
    mock_non_existent_file_path.exists.assert_called_once()

    # Test Case 4: File read IOError
    mock_io_error_file_path = MagicMock(spec=Path)
    mock_patterns_dir.__truediv__.reset_mock()
    mock_patterns_dir.__truediv__.return_value = mock_io_error_file_path
    mock_io_error_file_path.exists.return_value = True
    mock_io_error_file_path.open.side_effect = IOError("File read error")

    with pytest.raises(PatternNotFoundError) as excinfo:
        pattern_service.get_pattern_content("io_error_pattern")
    assert "Error reading pattern" in str(excinfo.value)
    mock_patterns_dir.__truediv__.assert_called_once_with("io_error_pattern.md")
    mock_io_error_file_path.exists.assert_called_once()
    mock_io_error_file_path.open.assert_called_once_with('r', encoding='utf-8')


def test_list_available_patterns(mocker):
    mock_patterns_dir = MagicMock(spec=Path)
    pattern_service = PatternService(mock_patterns_dir)

    mock_patterns_dir.is_dir.return_value = True

    # Mock Path objects that iterdir would return
    mock_p1_md = MagicMock(spec=Path)
    mock_p1_md.is_file.return_value = True
    mock_p1_md.suffix = ".md"
    mock_p1_md.stem = "p1"

    mock_p2_txt = MagicMock(spec=Path)
    mock_p2_txt.is_file.return_value = True
    mock_p2_txt.suffix = ".txt"
    mock_p2_txt.stem = "p2" # Should be filtered out

    mock_p3_md = MagicMock(spec=Path)
    mock_p3_md.is_file.return_value = True
    mock_p3_md.suffix = ".md"
    mock_p3_md.stem = "p3"

    mock_dir1 = MagicMock(spec=Path)
    mock_dir1.is_file.return_value = False # Directory, should be filtered out

    mock_ds_store = MagicMock(spec=Path) # e.g. .DS_Store
    mock_ds_store.is_file.return_value = True
    mock_ds_store.suffix = "" # No suffix, should be filtered out
    mock_ds_store.stem = ".DS_Store"

    mock_patterns_dir.iterdir.return_value = [
        mock_p1_md, mock_p2_txt, mock_p3_md, mock_dir1, mock_ds_store
    ]

    result = pattern_service.list_patterns()
    assert sorted(result) == sorted(['p1', 'p3'])
    mock_patterns_dir.is_dir.assert_called_once()
    mock_patterns_dir.iterdir.assert_called_once()


def test_clear_cache(mocker):
    mock_patterns_dir = MagicMock(spec=Path)
    pattern_service = PatternService(mock_patterns_dir)

    mock_file_path_for_cache = MagicMock(spec=Path)
    # Configure __truediv__ to consistently return this mock for "cache_test_pattern.md"
    def truediv_side_effect(pattern_filename):
        if pattern_filename == "cache_test_pattern.md":
            return mock_file_path_for_cache
        raise ValueError(f"Unexpected filename for __truediv__: {pattern_filename}")
    mock_patterns_dir.__truediv__.side_effect = truediv_side_effect

    mock_file_path_for_cache.exists.return_value = True
    # Configure mock_open to be reusable for multiple calls
    mock_opener = mock_open(read_data='initial content')
    mock_file_path_for_cache.open = mock_opener

    # Load a pattern to populate the cache
    pattern_service.get_pattern_content("cache_test_pattern")
    mock_opener.assert_called_once_with('r', encoding='utf-8')

    # Call clear_cache
    pattern_service.clear_cache()
    mock_opener.reset_mock() # Reset the mock for the next call verification

    # Load the same pattern again
    pattern_service.get_pattern_content("cache_test_pattern")
    # Assert 'open' was called again on the mock_opener
    mock_opener.assert_called_once_with('r', encoding='utf-8')
    # Check that exists was also called again
    assert mock_file_path_for_cache.exists.call_count == 2
