# Implementation Plan: KPIP Intelligence Innovations

This plan describes the phased roadmap for implementing the proposed intelligence innovations in the Kerala Police Intelligence Platform (KPIP). The focus is on transitioning the platform from a manual consolidation and heuristics-based database to an AI-assisted, phonetic-aware, relation-aware, and geographically mapped intelligence system.

---

## User Review Required

Please review the following high-level architectural decisions and priorities:

> [!IMPORTANT]
> **GPU / Resource Constraint Considerations**: The proposed Relational GNN (RGCN) and conversational RAG features run on local machine hardware. If the deployment environment (SSB Intranet) lacks dedicated GPUs, we should configure the models (Ollama, SentenceTransformers, and PyTorch GNN) to run in optimized CPU modes (quantized Qwen/Gemma weights, ONNX runtimes for SentenceTransformers).
>
> **Offline Geocoding Dependencies**: Since the platform operates in a secure intranet environment without internet access, any GIS hotspot mapping must rely on local geocoding databases (such as a local SQLite DB containing Kerala place coordinates or a static JSON boundary file) rather than external APIs like Google Maps or OpenStreetMap.

---

## Open Questions

We require guidance on these design and staging questions:
1. **Phasing Priority**: Should we execute Phase 1 (Dialect Suffixes & Entity Resolution) immediately as a first sprint, or would you prefer a different ordering (e.g., implementing the GIS Mapping first)?
2. **Local LLM Models**: What model sizes is your local Ollama server running? (e.g., Qwen2.5-7B, Gemma2-9B, or smaller models like 1.5B/3B?). This will help optimize RAG prompts and structured extraction execution times.

---

## Proposed Changes

We propose implementing the innovations across **four progressive phases**:

### Phase 1: Localized NLP & Advanced Entity Resolution (Core Pipelines)

We will expand name normalization to include regional Malayalam honorifics and nicknames, and replace simple TF-IDF name matching with phonetic matching (Double Metaphone) and context coreference resolution.

#### [MODIFY] [translation.py](file:///c:/projects/Digital%20University%20Project/Code/translation.py)
* Add support for regional Malayalam suffixes (e.g., `ഭായ്`, `സേഠ്`, `ചേട്ടൻ`, `ഇക്ക`, `അണ്ണൻ`).
* Add prefix-scanning logic to parse native place prefixes associated with names (e.g., *"Karippur Shaji"* → *"Shaji"* with metadata field `native_place: "Karippur"`).

#### [MODIFY] [ner_engine.py](file:///c:/projects/Digital%20University%20Project/Code/ner_engine.py)
* Integrate phonetic key generation (Double Metaphone algorithm) for all extracted names.
* Replace the simple TF-IDF name matching with context comparison of fields (father's name, residence address, and police station boundaries).
* Fallback to the local Ollama LLM to compare context paragraphs when a name matches multiple profiles (Cross-Document Coreference Resolution).

---

### Phase 2: Relational GNNs (RGCN) & Temporal Weight Decay (Network Layer)

We will modify the graph schema in Neo4j to incorporate chronological weight decay and upgrade the training logic in PyTorch from a homogeneous GCN to a Relational Graph Convolutional Network (RGCN).

#### [MODIFY] [graph_db.py](file:///c:/projects/Digital%20University%20Project/Code/graph_db.py)
* Update `add_relation` to apply temporal decay to edge weights. The weight of older edges will decay exponentially over time based on the elapsed days since the report date.
* Replace the TF-IDF feature vectors of graph nodes with high-quality sentence embeddings generated via the `QdrantService` SentenceTransformer.
* Update `GNNModelManager` to use an RGCN network architecture (supporting relation-type weights for `ACCUSED_IN`, `MEMBER_OF`, `CO_OCCURRED_WITH`, etc.) instead of a homogeneous GCN.

#### [MODIFY] [graph_service.py](file:///c:/projects/Digital%20University%20Project/Code/backend/app/services/graph_service.py)
* Expose endpoints to query the temporal graph (e.g., returning only relationships active during a specified date range).
* Update GNN recommendation hooks to serve the updated RGCN node similarities.

---

### Phase 3: Conversational RAG Intelligence Agent & MO Signatures (AI Agent Layer)

We will create a local RAG pipeline that combines Qdrant vector retrieval and Neo4j subgraph contexts to answer natural language questions about suspects.

#### [NEW] [rag_service.py](file:///c:/projects/Digital%20University%20Project/Code/backend/app/services/rag_service.py)
* Create a service that queries Qdrant for semantic documents and queries Neo4j for connected suspect nodes.
* Format a prompt containing both textual reports and node relationships, and invoke Ollama to generate an aggregated intelligence report.

#### [MODIFY] [routes.py](file:///c:/projects/Digital%20University%20Project/Code/backend/app/api/routes.py)
* Add a `/search/chat` endpoint to handle streaming RAG responses.

#### [MODIFY] [stubs.tsx](file:///c:/projects/Digital%20University%20Project/Code/frontend/src/features/stubs.tsx)
* Add a conversational chat interface in the frontend Search Page, allowing users to ask natural language questions and see structured source citations.

---

### Phase 4: Geospatial Intelligence Mapping (GIS Visualization Layer)

We will resolve coordinates of Kerala locations offline and plot suspect activities on a frontend interactive heatmap.

#### [NEW] [geocoding_service.py](file:///c:/projects/Digital%20University%20Project/Code/backend/app/services/geocoding_service.py)
* Implement an offline location database mapping common Kerala cities, villages, and police stations to lat-long coordinates.
* Extract geographic entities from ingested documents and append geocoordinates to record objects.

#### [MODIFY] [stubs.tsx](file:///c:/projects/Digital%20University%20Project/Code/frontend/src/features/stubs.tsx)
* Integrate Leaflet.js map panels in place of current stubs.
* Implement incident heatmaps and draw network relationship lines directly on top of the map.

---

## Verification Plan

### Automated Tests
* Execute unit tests for dialect anchoring and place prefix parsing:
  `python -m pytest tests/test_translation.py` (or execute via backend shell).
* Verify GNN training outputs by printing node embedding similarities:
  `python Code/graph_db.py --train` (or similar test harness).

### Manual Verification
* Upload test report `.docx` containing dialect suffixes and verify that the translation is correctly normalized without literal names translation.
* Perform semantic queries on the newly added RAG page and inspect that response aggregates verify against raw documents.
* Open the Graph Explorer and verify that relation-specific recommendations display as expected.
* View the Leaflet GIS interface in the browser to verify coordinates map correctly.
