import sys
import os

# Local development (4 levels up)
root_local = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Docker container (3 levels up, i.e., /app)
root_docker = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.path.exists(os.path.join(root_local, "backend", "app", "infrastructure", "documents", "utils.py")):
    ROOT_DIR = root_local
    APP_BASE = os.path.join(ROOT_DIR, "backend", "app")
else:
    ROOT_DIR = root_docker
    APP_BASE = os.path.join(ROOT_DIR, "app")

# Add root and infrastructure/module directories to path for legacy support
directories = [
    ROOT_DIR,
    os.path.join(APP_BASE, "infrastructure", "neo4j"),
    os.path.join(APP_BASE, "infrastructure", "nlp"),
    os.path.join(APP_BASE, "infrastructure", "translation"),
    os.path.join(APP_BASE, "infrastructure", "documents"),
    os.path.join(APP_BASE, "infrastructure", "ollama"),
    os.path.join(APP_BASE, "infrastructure", "qdrant"),
    os.path.join(APP_BASE, "modules", "graph"),
    os.path.join(APP_BASE, "modules", "reports"),
    os.path.join(APP_BASE, "modules", "profiles"),
    os.path.join(APP_BASE, "modules", "review"),
    os.path.join(APP_BASE, "modules", "consolidation"),
    os.path.join(APP_BASE, "modules", "search"),
    os.path.join(APP_BASE, "cli"),
]

for d in directories:
    if os.path.exists(d) and d not in sys.path:
        sys.path.insert(0, d)
