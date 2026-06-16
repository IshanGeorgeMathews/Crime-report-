# debug-neo4j-graph-crash

**Status:** [OPEN]
**Session ID:** `neo4j-graph-crash`
**Symptom:** Server crashes after a request to inspect the Neo4j graph (most likely `/api/v1/graph/query?queryType=semantic` or `/api/v1/graph/associates/{name}`) when running inside Docker.
**Repro so far:** Triggered after the user runs a graph inspection request while the API container is up. The container stops responding; user perceives this as a "crash".
**Env:** Docker Compose stack — `api` + `postgres` + `redis` + `neo4j:5-community` + `qdrant` + `ollama`.

> No business-logic changes allowed until post-fix evidence is collected. The only allowed first diff is instrumentation.

---

## Hypotheses (falsifiable, ordered by likelihood)

### H1 — Synchronous PyTorch GCN training OOMs / blocks the worker
**Observation point:** `backend/app/services/graph_service.py:46` → `GNNModelManager.train(epochs=50)` is called **inline** from `get_associates`, which is called from the sync path of an `async` route (`/api/v1/graph/associates/{person_name}`).
**Why this crashes:** For any non-trivial graph (≥ a few hundred nodes), the path:
1. loads every node's `description` from Neo4j,
2. fits a `TfidfVectorizer` over them,
3. builds a dense `N×N` adjacency (`A = np.zeros((N,N))`),
4. runs a 50-epoch GCN training loop with full-batch forward/backward.

…can either OOM the worker (Docker default `mem_limit` on the API container is unset, but the host's Docker memory limit is 8 GB) or block for tens of seconds, causing the client to time out and the user to perceive a "crash".
**Falsify by:** log training start/end time, `len(all_nodes)`, `X.shape`, `A.shape`; if OOM, exit code 137 is visible in `docker compose logs api`.

### H2 — `urllib.request.urlopen` to the debug server (port 7777) hangs without a timeout
**Observation point:** inline `exec(...)` probes at
- `backend/app/api/routes.py:749`
- `backend/app/services/graph_service.py:349`
- `backend/app/services/graph_service.py:452`

`urllib.request.urlopen(...)` is called with **no `timeout=` argument**. If `127.0.0.1:7777` is reachable from inside the API container (host port 7777 is bound on the host), but the host debug server is slow, the call blocks indefinitely. The FastAPI threadpool (default 40 threads) is consumed by these probes, then new requests hang and the container is restarted by `docker compose` / the orchestrator.
**Falsify by:** log the wall-clock duration of each `urlopen` and whether it raised `TimeoutError`, `ConnectionRefusedError`, or returned. Add `timeout=2` to the request and re-test.

### H3 — The `_find_crime_seed_node_ids` Cypher query hits a parameter-binding error
**Observation point:** `backend/app/services/graph_service.py:464`. The Cypher uses `$search_text` (a string) and `$tokens` (a Python list) and runs:
```cypher
any(token IN $tokens WHERE toLower(coalesce(c.text, '')) CONTAINS token OR ...)
```
If `$tokens` is empty AND `$search_text` is empty, the driver still serialises the query, but Neo4j may reject empty list parameters or the planner may produce a degenerate plan. Also, in some neo4j-driver versions, passing a Python `list` of strings as `$tokens` and using it in an `any(... IN $list WHERE ...)` clause can fail with `ClientError`.
**Falsify by:** log the result of `self.db._run(...)` and any exception text; log the `type(tokens)` and `len(tokens)` before the call.

### H4 — `GraphDatabase.__init__` opens a Neo4j driver at import time and never closes it
**Observation point:** `graph_db.py:73` `GraphDatabase.__init__` creates `Neo4jDriver.driver(uri, auth=auth)` and stores `self._driver`. The instance is created at `backend/app/services/graph_service.py:11` (`graph_service = GraphService()`) **at module import time** — i.e. before the FastAPI lifespan hook can guarantee Neo4j is reachable. When the container starts, the driver is constructed with the env values from `docker-compose.yml`; if Neo4j is not yet up, the driver still constructs a connection pool, then the first real query fails. Worse, the driver is a module-level singleton; on container restart it leaks handles.
**Falsify by:** log `is_connected()` immediately after `__init__`; on a clean restart, log `len(self._driver._pool.connections)` (private API) or simply log when first query is attempted and the delta from import time.

### H5 — Audit log file (`graph_db_audit.json`) grows unbounded and JSON parse/write OOMs
**Observation point:** `graph_db.py:163` `_log_audit` does `json.load` + `append` + `json.dump` on every write. During a semantic graph query that touches many nodes (and the build_semantic_subgraph loop iterates multiple times), this file grows by one entry per node visited. After a few runs of consolidation, the file is several MB; loading it on every write becomes the dominant cost, and the API container's CPU pins at 100% during graph queries.
**Falsify by:** log `os.path.getsize(self._audit_path)` and the `len(logs)` after each `_log_audit` call; sample a few query durations.

---

## Plan

1. **Step 1 (now):** Add minimal non-intrusive instrumentation. Three new `#region debug-point` lines, no logic change:
   - Wrap each of the three existing `exec(...)` probes in a measured wrapper that records wall-clock duration and result.
   - Add an instrumentation point at the **start** of `get_associates` (H1) and at the **start** of `GNNModelManager.train` (H1) that logs `len(all_nodes)`, `epochs`, and process RSS (`resource.getrusage`).
   - Add an instrumentation point around `_find_crime_seed_node_ids` (H3) that logs `len(tokens)` and the call duration.
   - Add an instrumentation point in `GraphDatabase.__init__` (H4) that logs the timestamp of driver construction.
   - Add an instrumentation point in `_log_audit` (H5) that logs the file size every 50 calls.
2. **Step 2:** User reproduces the crash.
3. **Step 3:** Read `.dbg/trae-debug-log-neo4j-graph-crash.ndjson` to confirm/reject each hypothesis.
4. **Step 4:** Apply a **minimal** fix targeted at the confirmed hypothesis.
5. **Step 5:** Re-run; compare pre-fix vs post-fix log lines for that hypothesis.
6. **Step 6 (only after user confirms "Fixed"):** Remove all instrumentation and delete the debug file.

---

## Files of interest

- [backend/app/api/routes.py:728-799](file:///c:/projects/Digital%20University%20Project/Code/backend/app/api/routes.py#L728) — `/api/v1/graph/query` route
- [backend/app/api/routes.py:826-829](file:///c:/projects/Digital%20University%20Project/Code/backend/app/api/routes.py#L826) — `/api/v1/graph/associates/{person_name}` route
- [backend/app/services/graph_service.py:46-67](file:///c:/projects/Digital%20University%20Project/Code/backend/app/services/graph_service.py#L46) — `get_associates` (calls `gnn.train`)
- [backend/app/services/graph_service.py:444-475](file:///c:/projects/Digital%20University%20Project/Code/backend/app/services/graph_service.py#L444) — `_find_crime_seed_node_ids` (H3)
- [backend/app/services/graph_service.py:103](file:///c:/projects/Digital%20University%20Project/Code/backend/app/services/graph_service.py#L103) — `query_subgraph` f-string depth
- [graph_db.py:73](file:///c:/projects/Digital%20University%20Project/Code/graph_db.py#L73) — `GraphDatabase.__init__`
- [graph_db.py:163](file:///c:/projects/Digital%20University%20Project/Code/graph_db.py#L163) — `_log_audit`

---

## Out of scope (acknowledge but not now)

- The seed users `admin/admin`, the `get_current_user` dummy-admin fallback, the mock-mode default in `frontend/.env` — these are separate hardening items tracked in the audit report.
- Replacing the GCN with a non-PyTorch link predictor — large refactor; only consider if H1 confirms.
