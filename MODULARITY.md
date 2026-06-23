# Modular Codebase Structure

The Kerala Police Intelligence Platform (KPIP) codebase has been restructured to be more modular, manageable, and easier to extend.

## Directory Structure

- `backend/app/infrastructure/`: Foundational logic for external services (Neo4j, Qdrant, Ollama, NLP, Translation).
- `backend/app/modules/`: Domain-specific logic (Consolidation, Reports, Graph, Profiles, Review, Search).
- `backend/app/cli/`: Command-line interface tools for interacting with the platform.
  - `intel_tool.py`: Main CLI for report consolidation, profile syncing, and UO generation.
- `scripts/`: Maintenance, setup, and diagnostic scripts.
  - `db_migrations.py`: Neo4j index and constraint setup.
  - `cleanup_junk_profiles.py`: Script to remove invalid profiles.
  - `verify_preflight.py`: Pre-consolidation dependency checker.
- `tests/`: Automated and manual test scripts.
  - `test.py`: Basic connectivity and functionality tests.
- `backend/`: FastAPI backend application.
- `frontend/`: React-based web frontend.

## Benefits of Modularity

1.  **Easier Testing**: Core components can now be tested independently by adding scripts to the `tests/` directory.
2.  **Clearer Organization**: Separating core logic from CLI tools and maintenance scripts makes the codebase more navigable for new developers.
3.  **Simplified Extensibility**: Adding new features or components (e.g., a new data ingestion source or a different LLM service) is easier as the boundaries between modules are well-defined.
4.  **Manageable Dependencies**: Modules have clearer import paths, reducing the risk of circular dependencies and making it easier to manage requirements.

## How to use and extend

### Running the CLI
To use the main CLI tool:
```bash
python cli/intel_tool.py --help
```

### Extending Core Logic
To add new core functionality, create a new file in the `core/` directory and include an `__init__.py` if necessary. Other modules can then import it using `from core.module_name import ...` (ensure `core/` is in your `sys.path`).

### Adding Scripts
New maintenance or setup scripts should be placed in the `scripts/` directory. They should include the boilerplate to add `core/` to their `sys.path` to access core functionality.
