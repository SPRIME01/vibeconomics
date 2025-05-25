import sys
from pathlib import Path

# Add the src directory to the Python path for proper imports
src_root = Path(__file__).parent / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))
