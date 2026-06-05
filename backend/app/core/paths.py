import sys
import os

# Local development (4 levels up)
root_local = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Docker container (3 levels up, i.e., /app)
root_docker = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.path.exists(os.path.join(root_local, "utils.py")):
    ROOT_DIR = root_local
else:
    ROOT_DIR = root_docker

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
