import sys
from pathlib import Path

# Add project root to sys.path to allow imports from core and gui
sys.path.insert(0, str(Path(__file__).parent))

# Start the application
from gui.app import *  # noqa