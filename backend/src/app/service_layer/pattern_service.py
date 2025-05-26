from pathlib import Path
import os
from typing import Dict, List

class PatternNotFoundError(Exception):
    pass

class PatternService:
    def __init__(self, patterns_dir_path: Path) -> None:
        self.patterns_dir_path: Path = patterns_dir_path
        self._cache: Dict[str, str] = {}

    def get_pattern_content(self, pattern_name: str) -> str:
        if pattern_name in self._cache:
            return self._cache[pattern_name]

        file_path: Path = self.patterns_dir_path / f"{pattern_name}.md"

        if not file_path.exists():
            raise PatternNotFoundError(f"Pattern '{pattern_name}' not found at {file_path}")

        try:
            with file_path.open('r', encoding='utf-8') as f:
                content: str = f.read()
            self._cache[pattern_name] = content
            return content
        except IOError as e:
            raise PatternNotFoundError(f"Error reading pattern '{pattern_name}' from {file_path}: {e}") from e

    def list_patterns(self) -> List[str]:
        pattern_names: List[str] = []
        if not self.patterns_dir_path.is_dir():
            # Or raise an error, or return empty list, depending on desired behavior
            return [] 
        for item in self.patterns_dir_path.iterdir():
            if item.is_file() and item.suffix == '.md':
                pattern_names.append(item.stem)
        return pattern_names

    def clear_cache(self) -> None:
        self._cache.clear()
