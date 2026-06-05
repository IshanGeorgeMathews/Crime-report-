import sys
import os

# Get the absolute path of the root directory containing the existing modules
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
