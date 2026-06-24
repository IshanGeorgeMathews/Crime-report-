# Critical Issues Report - Kerala Police Intelligence Platform (KPIP)

## 1. GNN Training Blocks Event Loop (H1)
**Location:** `backend/app/services/graph_service.py`, `_get_gnn()`
**Issue:** PyTorch GCN training (50 epochs) is performed synchronously within the request-response cycle of the `/api/v1/graph/associates/{person_name}` endpoint.
**Impact:** For larger graphs, this will block the FastAPI worker thread for a significant duration, leading to timeouts, unresponsive API, and perceived "crashes". In a Docker environment with memory limits, large dense adjacency matrices could trigger OOM.

## 2. Driver Connection at Import Time (H4)
**Location:** `graph_db.py`, `GraphDatabase.__init__` and `backend/app/services/graph_service.py`
**Issue:** `GraphDatabase` is instantiated at the module level in `graph_service.py`. The `__init__` method immediately attempts to connect to Neo4j.
**Impact:** If Neo4j is not ready when the API container starts, the service may fail or enter an unstable state. It also makes testing difficult as it requires a live database just to import the module.

## 3. Potential for Request Hanging (H2)
**Location:** Identified in `debug-neo4j-graph-crash.md` (though not currently visible in the provided snippets, it's a documented risk).
**Issue:** Use of `urllib.request.urlopen` or `requests` without explicit timeouts in the backend logic.
**Impact:** If an external service (like Ollama or a debug server) is slow or unreachable, it can consume all available worker threads, leading to a total system hang.

## 4. Inefficient Audit Logging (H5)
**Location:** `graph_db.py`, `_log_audit`
**Issue:** The previous implementation (referenced in debug docs) used `json.load` + `append` + `json.dump`, which is $O(N)$ and OOM-prone.
**Current State:** The code now uses `jsonl` format (append-only), which is $O(1)$.
**Status:** This specific issue seems to have been partially addressed but should be verified for file size growth management.

## 5. Parameter Binding Risks in Cypher Queries (H3)
**Location:** `backend/app/services/graph_service.py` (Mode: DATE, Mode: CRIME)
**Issue:** Complex Cypher queries with potential for empty parameters or list-type mismatches.
**Impact:** Can cause Neo4j driver errors or degenerate query plans that pin CPU.

## 6. Lack of Proper Async Database Sessions in Services
**Location:** `backend/app/services/`
**Issue:** Many services (like `GraphService`, `NERService`) are instantiated as singletons but do not always handle async sessions or lifecycle correctly, often relying on global state or synchronous wrappers.
**Impact:** Potential for connection leaks or thread-safety issues under high concurrency.
