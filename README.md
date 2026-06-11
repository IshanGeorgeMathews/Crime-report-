# Kerala Police Intelligence Platform (KPIP)

A comprehensive intelligence report consolidation and suspect profile management system for the IS Division, SSB, Kerala Police.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Directory Structure](#directory-structure)
4. [Backend Components](#backend-components)
   - [FastAPI Application (backend/app)](#fastapi-application-backendapp)
   - [Core Modules (root level)](#core-modules-root-level)
5. [Data Models & Database Schema](#data-models--database-schema)
6. [API Endpoints](#api-endpoints)
7. [Services Layer](#services-layer)
8. [Graph Database (Neo4j)](#graph-database-neo4j)
9. [Vector Search (Qdrant)](#vector-search-qdrant)
10. [Translation Pipeline](#translation-pipeline)
11. [Consolidation Pipeline](#consolidation-pipeline)
12. [Frontend](#frontend)
13. [Deployment](#deployment)
14. [Configuration](#configuration)

---

## Project Overview

This platform automates the daily workflow of intelligence processing:

1. **Input Processing**: Reads intelligence documents (BACK FILES) containing events, forecasts, and social media reports
2. **Translation**: Translates Malayalam documents to English using IndicTrans2/Google Translate
3. **Classification**: Categorizes items as events, forecasts, social media, or low-priority
4. **Profile Matching**: Matches suspects mentioned in reports against existing Person Profile (PP) files
5. **Profile Creation**: Creates new PP profiles and UO Notes for newly identified suspects
6. **Graph Analysis**: Maintains relationship graphs (individuals ↔ crimes ↔ records) in Neo4j
7. **GNN Recommendations**: Uses Graph Neural Networks to predict hidden suspect associations
8. **Report Generation**: Generates consolidated Daily IS Reports in DOCX format

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│                   http://localhost:5173                          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST + SSE
┌────────────────────────────▼────────────────────────────────────┐
│                     FastAPI Backend                               │
│                   http://localhost:8000                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    API Routes (routes.py)                   │  │
│  │  /auth/*  /jobs/*  /reports/*  /profiles/*  /graph/*  ...  │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Services Layer                           │  │
│  │  ConsolidationService  ProfileService  GraphService  ...  │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   ┌────────────┐    ┌────────────┐    ┌────────────┐
   │  SQLite/   │    │   Neo4j    │    │   Qdrant   │
   │ PostgreSQL │    │  (Graph)   │    │  (Vector)  │
   └────────────┘    └────────────┘    └────────────┘
```

---

## Directory Structure

```
Digital University Project/
│
├── backend/                           # FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py              # All API endpoints
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── paths.py               # Python path configuration
│   │   │   └── security.py            # JWT auth & password hashing
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── models.py              # SQLAlchemy ORM models
│   │   │   └── session.py             # Database session management
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── consolidation_service.py  # Main consolidation pipeline
│   │   │   ├── graph_service.py       # Neo4j graph operations
│   │   │   ├── ner_service.py        # NER/review queue operations
│   │   │   ├── profile_service.py     # PP profile management
│   │   │   ├── qdrant_service.py     # Vector search operations
│   │   │   ├── llm_service.py        # LLM integration
│   │   │   └── translation_service.py # Translation operations
│   │   ├── config.py                  # Settings & configuration
│   │   ├── dependencies.py           # FastAPI dependencies (auth)
│   │   ├── main.py                   # FastAPI app entry point
│   │   └── schemas.py                # Pydantic request/response schemas
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── frontend/                          # React + TypeScript application
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AuthenticatedLayout.tsx
│   │   │   │   ├── ClassificationBanner.tsx
│   │   │   │   └── Sidebar.tsx
│   │   │   └── ui/
│   │   │       ├── Badge.tsx
│   │   │       ├── Button.tsx
│   │   │       └── Input.tsx
│   │   ├── features/
│   │   │   ├── _graph_block.tsx
│   │   │   └── stubs.tsx             # Page components (stubs)
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useConsolidate.ts
│   │   │   ├── useGraph.ts
│   │   │   ├── useProfiles.ts
│   │   │   ├── useQueue.ts
│   │   │   ├── useReports.ts
│   │   │   ├── useSearch.ts
│   │   │   └── useUsers.ts
│   │   ├── lib/
│   │   │   └── api.ts                # Axios API client
│   │   ├── stores/
│   │   │   ├── authStore.ts          # Zustand auth state
│   │   │   ├── filterStore.ts
│   │   │   └── uiStore.ts
│   │   ├── types/
│   │   │   ├── api.ts
│   │   │   ├── graph.ts
│   │   │   ├── job.ts
│   │   │   └── profile.ts
│   │   ├── App.tsx                   # React Router setup
│   │   └── main.tsx                  # React entry point
│   ├── package.json
│   └── vite.config.ts
│
├── docs/
│   └── frontend-system-architecture-plan.md
│
├── Code/                             # Root level Python modules (standalone)
│   ├── utils.py                      # Core utilities (parsing, matching, reports)
│   ├── graph_db.py                   # Neo4j graph database + GNN
│   ├── intel_tool.py                # CLI entry point
│   ├── ner_engine.py                 # Named Entity Recognition engine
│   ├── translation.py                # Malayalam translation engine
│   ├── script_segmenter.py           # Script segmentation utilities
│   ├── cleanup_junk_profiles.py      # Profile cleanup utility
│   ├── real_report_data.py           # Sample report data
│   ├── verify_preflight.py           # Preflight checks
│   ├── requirements.txt
│   └── ...
│
├── PP & Uo Note Dummy-.../           # Profile database (file-based)
│   └── PP & Uo Note Dummy/
│       ├── PP Form details.docx      # Profile template
│       ├── 1)  Person Name.docx     # Individual profiles
│       ├── 1a) UO Person Name.docx  # UO notes
│       └── review_registry.json      # Review queue registry
│
├── BACK FILES/                       # Input intelligence documents
│   └── dd.mm.yyyy/                  # Per-date folders
│       ├── TVM.docx                  # District forecast
│       ├── F1.docx                   # Numbered forecast
│       ├── SOCIALMEDIA.docx          # Social media reports
│       └── EventReport.docx         # Event reports
│
└── DAILY IS REPORT/                  # Output consolidated reports
    └── IS Daily report dd.mm.yyyy.docx
```

---

## Backend Components

### FastAPI Application (backend/app)

#### [config.py](backend/app/config.py)
**Purpose**: Centralized configuration using Pydantic Settings

Key settings:
- `DATABASE_URL`: SQLite locally, PostgreSQL in production
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Neo4j connection
- `QDRANT_HOST`, `QDRANT_PORT`: Qdrant vector DB
- `OLLAMA_URL`, `OLLAMA_MODEL`: LLM integration
- `UPLOAD_DIR`: Temporary file uploads
- `PP_DIR`: Profile database directory

#### [main.py](backend/app/main.py)
**Purpose**: FastAPI application factory and middleware setup

#### [dependencies.py](backend/app/dependencies.py)
**Purpose**: FastAPI dependency injection for authentication/authorization

Role-based access:
- `require_viewer`: Can view reports, profiles, graphs
- `require_analyst`: Can consolidate, upload files
- `require_supervisor`: Can review profiles, manage schedules
- `require_admin`: Full system access

#### [schemas.py](backend/app/schemas.py)
**Purpose**: Pydantic models for request/response validation

Key schemas:
- `UserLogin`, `UserResponse`, `TokenResponse`
- `JobResponse`, `JobEventResponse`
- `ReportResponse`, `ReportItemResponse`
- `ProfileResponse`, `ProfileDetailResponse`
- `SearchRequest`, `SearchResultResponse`
- `GraphQueryResponse`, `GraphNodeResponse`, `GraphEdgeResponse`

---

### Core Modules (root level)

#### [utils.py](Code/utils.py)
**Purpose**: Core utilities for intelligence processing

Key functions:

| Function | Purpose |
|----------|---------|
| `read_docx_paragraphs(path)` | Read DOCX paragraphs |
| `read_docx_full_text(path)` | Read full DOCX text |
| `is_malayalam(text)` | Detect Malayalam text |
| `translate_ml_to_en(text)` | Translate Malayalam → English |
| `categorise_back_files(folder)` | Categorize files by type |
| `extract_district_tag(text)` | Extract district tags like (KLM-EC) |
| `build_daily_report(...)` | Generate consolidated DOCX report |
| `build_less_priority_report(...)` | Generate low-priority DOCX report |
| `load_profile_database(dir)` | Load PP profiles from DOCX files |
| `find_matching_profiles(text, profiles)` | Fuzzy match profiles to text |
| `extract_person_names(text)` | Extract names using heuristics |
| `create_new_profile(...)` | Create new PP profile DOCX |
| `generate_uo_note_text(...)` | Generate UO note text |
| `save_uo_note(...)` | Save UO note DOCX |

Key classes:
- `PersonProfile`: In-memory representation of a PP profile DOCX
  - Parses key-value pairs from paragraphs
  - Parses relations table (Table 0)
  - Parses case details table (Table 1)

Constants:
- `DISTRICT_CODES`: TVM, KLM, PTA, ALP, KTM, IDK, EKM, TSR, PKD, MPM, KKD, WYD, KNR, KSD
- `SOCIAL_MEDIA_KEYWORDS`: ["socialmedia", "social media", "social_media"]
- `HONORIFICS`: Sri, Shri, Smt, Mr, Mrs, Ms, Dr

#### [graph_db.py](Code/graph_db.py)
**Purpose**: Neo4j graph database manager with GNN capabilities

Key class: `GraphDatabase`

Node types:
- `Individual`: Suspect/person of interest
- `Record`: Daily intelligence record
- `Crime`: Specific crime/incident
- `Organization`: Organizations involved
- `Case`: FIR/case information

Relationships:
- `ASSOCIATED_WITH`: Individual ↔ Crime
- `MENTIONED_IN`: Individual → Record
- `CO_OCCURRED_WITH`: Individual ↔ Individual
- `REPORTED_IN`: Crime → Record
- `MEMBER_OF`: Individual → Organization
- `ACCUSED_IN`: Individual → Case

Key methods:
- `add_individual(name, pp_id, ps, address, activity_type)` - Add/update individual
- `add_record(date_str, filepath)` - Add daily record
- `add_crime(crime_id, text, district, category, date_str)` - Add crime event
- `add_organization(org_name, remarks)` - Add organization
- `add_case(case_id, fir, sections, ps, brief)` - Add case
- `add_relation(u_id, v_id, rel_type, weight)` - Create relationship
- `_run(query, **params)` - Execute Cypher query
- `get_stats()` - Get graph statistics
- `query_subgraph(...)` - Query subgraph by node/date/crime

GNN Class: `GNNModelManager`
- `train(epochs)` - Train GCN model
- `recommend_associates(name, top_n)` - Get associate recommendations

#### [intel_tool.py](Code/intel_tool.py)
**Purpose**: CLI entry point for standalone operations

Commands:
```bash
python intel_tool.py consolidate <date>    # Generate daily report
python intel_tool.py sync-profiles <file>  # Sync profiles
python intel_tool.py generate-uo <profile> # Generate UO note
```

#### [ner_engine.py](Code/ner_engine.py)
**Purpose**: Named Entity Recognition for suspect identification

Key class: `NEREngine`

Key methods:
- `initialize_ner_pipeline()` - Load HuggingFace NER model
- `reconcile_arfr()` - Automatic Registry-Filesystem Reconciliation
  - Scans PP directory for `*_review.docx` files
  - Updates `review_registry.json`
- `get_status(name)` - Get suspect status (pending/approved/rejected)
- `approve_name(name)` - Approve a suspect
- `reject_name(name)` - Reject a suspect

Registry states:
- `pending`: Review profile exists, needs approval
- `approved`: Production profile exists
- `rejected`: Manually rejected

#### [translation.py](Code/translation.py)
**Purpose**: Malayalam to English translation with suffix anchoring

Key function: `TranslationEngine.translate_document()`

Features:
- **Suffix Anchoring**: Preserves proper names like "Kuttan" vs "child"
- **Script Segmentation**: Handles mixed-script text
- **IndicTrans2 Primary**: Best quality translation
- **Google Fallback**: When IndicTrans2 unavailable

Key regex patterns:
- `KUTTY_SUFFIX_RE`: Matches കുട്ടി (child) suffixes
- `PILLAI_SUFFIX_RE`: Matches പിള്ള (child) suffixes

---

## Data Models & Database Schema

### SQLAlchemy Models ([models.py](backend/app/db/models.py))

#### User
```
users
├── id (String, PK)           # UUID
├── username (String, unique)   # Login name
├── password_hash (String)      # Bcrypt hash
├── full_name (String)          # Display name
├── role (String)               # admin, supervisor, analyst, viewer
├── district (String)           # User's district
├── is_active (Boolean)         # Account status
├── last_login_at (DateTime)    # Last login timestamp
├── created_at (DateTime)       # Account creation
└── updated_at (DateTime)       # Last update
```

#### Job
```
jobs
├── id (String, PK)            # UUID
├── job_type (String)          # consolidation, profile_sync, etc.
├── status (String)            # received, running, completed, failed, cancelled, stopped
├── progress (Integer)          # 0-100
├── current_step (String)       # Human-readable status
├── input_params (JSON)        # Job parameters
├── result (JSON)              # Job result data
├── error_message (Text)        # Error details if failed
├── warnings (JSON)             # Warning messages
├── warning_count (Integer)     # Warning count
├── celery_task_id (String)     # Background task ID
├── created_by (String, FK)     # User who created
├── started_at (DateTime)       # Job start time
├── completed_at (DateTime)     # Job completion time
└── created_at (DateTime)       # Record creation
```

#### Report
```
reports
├── id (String, PK)            # UUID
├── report_date (String, unique)  # DD.MM.YYYY format
├── ref_number (String)        # Reference number
├── event_count (Integer)      # Number of events
├── forecast_count (Integer)   # Number of forecasts
├── social_media_count (Integer)  # Social media items
├── not_needed_count (Integer)   # Low priority items
├── validation_warnings (JSON)  # Validation warnings
├── created_by (String, FK)    # User who created
├── job_id (String)            # Associated job
└── created_at (DateTime)       # Record creation

└── items (relationship)       # One-to-many ReportItems
```

#### ReportItem
```
report_items
├── id (String, PK)            # UUID
├── report_id (String, FK)     # Parent report
├── category (String)          # event, forecast, social_media, not_needed
├── sort_order (Integer)       # Display order
├── raw_text (Text)           # Original text
├── translated_text (Text)     # English translation
├── summary_text (Text)        # LLM summary
├── source_filename (String)   # Source file
├── district_tag (String)       # e.g., (KLM-EC)
├── translation_engine (String) # Translation method used
├── llm_model (String)         # Summarization model
└── created_at (DateTime)       # Record creation

└── report (relationship)      # Many-to-one Report
```

#### Profile
```
profiles
├── id (String, PK)            # UUID
├── pp_id (String, unique)    # PP number (e.g., PP-123)
├── name (String, indexed)    # Person's name
├── parentage (String)         # Parent's name
├── address (Text)             # Full address
├── police_station (String)    # PS name
├── dob (String)              # Date of birth
├── place_of_birth (String)
├── qualification (String)
├── religion (String)
├── identification_marks (Text)
├── mobile (String)
├── activity_type (String)     # e.g., Extremist, Smuggler
├── reason_for_inclusion (Text)
├── organization_name (String)
├── organization_remarks (Text)
├── brief_history (Text)
├── review_status (String)     # approved, pending, rejected
├── neo4j_node_id (String)     # Link to Neo4j
├── reviewed_by (String, FK)   # Reviewer user
├── reviewed_at (DateTime)     # Review time
├── created_at (DateTime)
└── updated_at (DateTime)

└── cases (relationship)       # One-to-many ProfileCases
└── relations (relationship)  # One-to-many ProfileRelations
└── activities (relationship)  # One-to-many ProfileActivities
```

#### ProfileCase
```
profile_cases
├── id (String, PK)
├── profile_id (String, FK)
├── fir_number (String)        # FIR number
├── under_sections (Text)      # Legal sections
├── police_station (String)
├── case_brief (Text)
├── case_status (String)        # Under Investigation, etc.
├── co_accused (Text)          # Co-accused names
└── neo4j_case_node_id (String)
```

#### ProfileRelation
```
profile_relations
├── id (String, PK)
├── profile_id (String, FK)
├── name (String)              # Relative name
├── relation_type (String)      # Father, Mother, Spouse, etc.
├── address (Text)
└── mobile (String)
```

#### ProfileActivity
```
profile_activities
├── id (String, PK)
├── profile_id (String, FK)
├── activity_name (String)
├── activity_desc (Text)
├── activity_date (String)     # DD.MM.YYYY
├── report_id (String)          # Source report
└── created_at (DateTime)
```

#### JobEvent
```
job_events
├── id (Integer, PK, autoincrement)
├── job_id (String, FK)
├── status (String)
├── progress (Integer)
├── message (Text)
└── created_at (DateTime)
```

#### AuditLog
```
audit_log
├── id (Integer, PK, autoincrement)
├── user_id (String, FK)
├── username (String)
├── action (String)            # Action type
├── entity_type (String)       # Target entity type
├── entity_id (String)         # Target entity ID
├── details (JSON)             # Action details
├── ip_address (String)
├── user_agent (String)
└── created_at (DateTime)
```

---

## API Endpoints

All endpoints are under `/api/v1`. See [routes.py](backend/app/api/routes.py) for full implementation.

### Authentication (`/auth/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login, returns JWT |
| GET | `/auth/me` | Get current user info |
| POST | `/auth/logout` | Logout (audit only) |
| POST | `/auth/change-password` | Change password |

### Jobs (`/jobs/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs` | List recent jobs |
| GET | `/jobs/{job_id}` | Get job details |
| GET | `/jobs/{job_id}/events` | SSE stream for job progress |
| POST | `/jobs/{job_id}/cancel` | Cancel running job |
| POST | `/jobs/{job_id}/stop` | Pause/stop job |

### Consolidation (`/consolidate/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/consolidate/upload` | Upload files for consolidation |

### Reports (`/reports/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports` | List all reports |
| GET | `/reports/{id}` | Get report with items |
| GET | `/reports/{id}/download` | Download daily report DOCX |
| GET | `/reports/{id}/less-priority/download` | Download LP report DOCX |

### Profiles (`/profiles/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/profiles` | List profiles |
| GET | `/profiles/{id}` | Get profile details |
| GET | `/profiles/{id}/docx` | Download profile DOCX |
| PUT | `/profiles/{id}` | Update profile |
| GET | `/profiles/{id}/cases` | Get profile cases |
| GET | `/profiles/{id}/relations` | Get profile relations |
| GET | `/profiles/{id}/activities` | Get profile activities |

### Graph (`/graph/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/graph/stats` | Get graph statistics |
| POST | `/graph/query` | Query subgraph |
| POST | `/graph/associates` | Get GNN associate recommendations |
| DELETE | `/graph/clean` | Clean junk nodes |

### Search (`/search/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/search/semantic` | Vector similarity search (Qdrant) |
| POST | `/search/structured` | SQL keyword search |
| POST | `/search/semantic-nlp` | NLP-enhanced semantic search |

### Admin (`/admin/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/users` | List users |
| POST | `/admin/users` | Create user |
| PUT | `/admin/users/{id}` | Update user |
| DELETE | `/admin/users/{id}` | Delete user |
| GET | `/admin/audit` | Get audit log |

### NER/Review (`/ner/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ner/review-queue` | Get pending review items |
| POST | `/ner/approve/{name_id}` | Approve suspect |
| POST | `/ner/reject/{name_id}` | Reject suspect |
| POST | `/ner/sync` | Sync profiles from filesystem |

### System (`/system/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/system/status` | System health status |
| GET | `/system/config` | Public configuration |

---

## Services Layer

### [ConsolidationService](backend/app/services/consolidation_service.py)

Main consolidation pipeline orchestrator.

**Key methods:**

`run_consolidation(job_id, date_str, source_files_dir)`
- Executes the full pipeline asynchronously
- Steps:
  1. Initialize job status
  2. Translate Malayalam files
  3. Classify and summarize items
  4. Match profiles
  5. Sync to Neo4j
  6. Index in Qdrant
  7. Build DOCX reports

`update_job(db, job_id, status, progress, current_step, ...)`
- Updates job status in DB
- Creates JobEvent for SSE stream

`cancel_job(job_id, source_files_dir)`
- Rolls back all changes
- Deletes Report/ReportItem rows
- Removes Neo4j nodes for the date
- Cleans up temp files

`stop_job(job_id)`
- Pauses job, preserving state

### [ProfileService](backend/app/services/profile_service.py)

Manages PP profile DOCX files and DB sync.

**Key methods:**

`sync_all_profiles_to_db(db)`
- Loads all profiles from PP_DIR
- Reconciles production vs review files
- Creates/updates Profile records
- Parses relations, cases, activities

`get_profile_docx_path(profile_name, prefer_review)`
- Finds matching DOCX file for a profile name

### [GraphService](backend/app/services/graph_service.py)

Neo4j graph operations wrapper.

**Key methods:**

`get_stats()`
- Returns node/edge counts by type

`query_subgraph(center_node_id, depth, query_type, date, crime_keyword)`
- Query by: `all`, `date`, `crime`, `node`
- Returns `{nodes: [], edges: []}`

`get_associates(person_name, top_n)`
- Trains GNN
- Returns top N associate recommendations

### [QdrantService](backend/app/services/qdrant_service.py)

Vector similarity search.

**Key methods:**

`embed(text)` - Generate 384-dim vector
`upsert_item(collection, point_id, text, payload)` - Add/update item
`search(collection, query, limit)` - Vector similarity search

Collections:
- `report_items` - Report item summaries
- `profiles` - Profile descriptions
- `crimes` - Crime descriptions

### [NERService](backend/app/services/ner_service.py)

Named Entity Recognition for suspect review queue.

**Key methods:**

`get_review_queue()`
- Runs ARFR reconciliation
- Returns pending review candidates

`approve_candidate(name_id)`
- Approves suspect
- Renames `*_review.docx` to production

`reject_candidate(name_id)`
- Marks suspect as rejected
- Deletes review file

---

## Graph Database (Neo4j)

### Connection
```python
from graph_db import GraphDatabase
db = GraphDatabase(
    uri="bolt://localhost:7687",
    auth=("neo4j", "password"),
    database="prosecutorreport"
)
```

### Node IDs
- Individuals: `ind_{name_lower_underscored}` (e.g., `ind_arippa_pull}`)
- Records: `rec_{date_underscored}` (e.g., `rec_10_03_2022`)
- Crimes: `cri_{crime_id}` (e.g., `cri_1`)
- Organizations: `org_{name_lower_underscored}`
- Cases: `case_{fir_lower_underscored}`

### Cypher Query Examples

**Get all nodes linked to a date:**
```cypher
MATCH (rec)-[r]-(neighbor)
WHERE rec.type = 'record' AND rec.date = $date
RETURN rec AS a, type(r) AS rel_type, properties(r) AS props, neighbor AS b
```

**Get crime by keyword:**
```cypher
MATCH (c)
WHERE c.type = 'crime' AND toLower(c.text) CONTAINS $kw
MATCH (c)-[r]-(neighbor)
RETURN c AS a, type(r) AS rel_type, properties(r) AS props, neighbor AS b
```

---

## Vector Search (Qdrant)

### Connection
```python
from qdrant_service import QdrantService
qdrant = QdrantService()
```

### Search Flow
1. Query text → SentenceTransformer → 384-dim vector
2. Qdrant returns similar points by cosine similarity
3. Results enriched with DB metadata

### Fallback
If Qdrant unavailable, falls back to SQL `LIKE` queries with keyword matching.

---

## Translation Pipeline

### Flow
```
Malayalam Text
    │
    ▼
┌─────────────────────┐
│ IndicTrans2 Model   │ ◄── Primary translator
│ (ai4bharat/indic   │
│  trans2-indic-en)   │
└─────────┬───────────┘
          │ (if fails)
          ▼
┌─────────────────────┐
│ Google Translator   │ ◄── Fallback
│ (deep-translator)   │
└─────────┬───────────┘
          │
          ▼
    English Text
```

### Suffix Anchoring ([translation.py](Code/translation.py))
Prevents mistranslation of names:
- കുട്ടി (child) → anchored as "Kuttan" (proper name suffix)
- പിള്ള → anchored as "Pillai"

Uses backward-scanning context evaluation to distinguish names from common nouns.

---

## Consolidation Pipeline

### Full Flow
```
User uploads .docx files
         │
         ▼
┌────────────────────────┐
│ 1. Save to temp dir    │
│ 2. Create Job record   │
└─────────┬──────────────┘
          │
          ▼
┌────────────────────────────────────────┐
│ 3. Run consolidation async              │
│    ┌───────────────────────────────┐   │
│    │ a. Read each .docx file       │   │
│    │ b. Extract paragraphs         │   │
│    │ c. Detect Malayalam           │   │
│    │ d. Translate (IndicTrans2)    │   │
│    │ e. Classify (event/forecast/ │   │
│    │    social_media/not_needed)   │   │
│    │ f. Summarize (Gemma via       │   │
│    │    Ollama, if available)      │   │
│    │ g. Extract district tags       │   │
│    └───────────────────────────────┘   │
└─────────┬──────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────┐
│ 4. Create Report + ReportItems         │
│    - Store in SQLite                   │
│    - Index in Qdrant                   │
└─────────┬──────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────┐
│ 5. Sync to Neo4j                      │
│    - Create Record node                │
│    - Create Crime nodes                │
│    - Create Individual nodes           │
│    - Create relationships             │
└─────────┬──────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────┐
│ 6. Profile matching                    │
│    - Extract person names              │
│    - Fuzzy match to existing profiles │
│    - Flag new suspects for review      │
└─────────┬──────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────┐
│ 7. Build DOCX reports                  │
│    - Daily IS Report: events,         │
│      forecasts, social media           │
│    - Less Priority Report: filtered   │
│      items for human review           │
└─────────┬──────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────┐
│ 8. Mark job complete                   │
│    - Update Job status                 │
│    - Store result summary              │
└────────────────────────────────────────┘
```

### Cancellation/Stop
- **Stop**: Preserves state, can resume
- **Cancel**: Rolls back all changes (DB, Neo4j, files)

---

## Frontend

### Tech Stack
- React 19 + TypeScript
- Vite (build tool)
- React Router v7 (routing)
- TanStack Query (data fetching)
- Zustand (state management)
- TailwindCSS (styling)
- Axios (HTTP client)

### State Management
- `authStore`: User authentication state
- `filterStore`: Global filters
- `uiStore`: UI state (sidebar, modals)

### Key Hooks
- `useAuth()`: Authentication operations
- `useConsolidate()`: Upload and job tracking
- `useReports()`: Report listing and details
- `useProfiles()`: Profile management
- `useGraph()`: Graph queries
- `useSearch()`: Search operations
- `useQueue()`: Job queue tracking

### Pages (stubs.tsx)
- `LoginPage` - Authentication
- `DashboardPage` - Overview
- `ConsolidatePage` - File upload
- `QueuePage` - Job tracking
- `ReviewQueuePage` - Suspect review
- `ReportListPage` - Report listing
- `ReportDetailPage` - Report details
- `ProfileListPage` - Profile listing
- `ProfileDetailPage` - Profile details
- `GraphExplorerPage` - Graph visualization
- `SearchPage` - Search interface
- `SchedulePage` - Scheduled tasks
- `UserManagementPage` - User admin
- `AuditTrailPage` - Audit logs
- `SystemStatusPage` - Health checks

---

## Deployment

### Docker Compose

See [docker-compose.yml](backend/docker-compose.yml)

```yaml
Services:
  api:          # FastAPI application
  postgres:     # PostgreSQL 15
  redis:        # Redis 7 (for future caching)
  neo4j:        # Neo4j 5 Community
  qdrant:       # Qdrant vector DB
  ollama:       # Ollama (LLM inference)
```

### Environment Variables

**API Service:**
```bash
DATABASE_URL=postgresql+asyncpg://kpip:DigitalUniversity@postgres:5432/kpip
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=DigitalUniversity
QDRANT_HOST=qdrant
QDRANT_PORT=6333
OLLAMA_URL=http://ollama:11434
```

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### Production Build
```bash
# Backend
cd backend
docker build -t kpip-api .

# Frontend
cd frontend
npm run build
```

---

## Configuration

### Settings ([config.py](backend/app/config.py))

| Setting | Default | Description |
|---------|---------|-------------|
| `PROJECT_NAME` | Kerala Police Intelligence Platform | Project title |
| `SECRET_KEY` | (change in prod) | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 480 | Token expiry (8 hours) |
| `DATABASE_URL` | sqlite+aiosqlite:///./kpip.db | Database connection |
| `NEO4J_URI` | bolt://localhost:7687 | Neo4j URI |
| `NEO4J_DATABASE` | prosecutorreport | Neo4j database |
| `QDRANT_HOST` | localhost | Qdrant host |
| `QDRANT_PORT` | 6333 | Qdrant port |
| `OLLAMA_URL` | http://localhost:11434 | Ollama URL |
| `OLLAMA_MODEL` | qwen:8b | Default LLM model |

### Directory Paths
- `UPLOAD_DIR`: Temporary file uploads
- `PP_DIR`: Profile database (DOCX files)

---

## Security

### Authentication
- JWT tokens with 8-hour expiry
- Token contains: user_id, role, district
- Refresh on each request via Authorization header

### Authorization (RBAC)
| Role | Permissions |
|------|------------|
| viewer | View reports, profiles, graphs, search |
| analyst | + Consolidate, upload, job management |
| supervisor | + Review suspects, schedules |
| admin | + User management, audit logs |

### Password Security
- Bcrypt hashing
- Minimum 8 characters

---

## File Processing

### Back Files Categorization

Files are categorized by:

1. **Filename patterns:**
   - Contains "socialmedia" → social_media
   - District code (TVM, KLM, etc.) → forecast
   - F-prefix (F1, F2) → forecast
   - Everything else → event

2. **Content-based fallback:**
   - `/RSU/` in content → social_media
   - `/CC/` in content → forecast
   - `/EC/` in content → event
   - Keywords: "forecast", "alert", "scheduled" → forecast
   - Keywords: "social media", "facebook", "twitter" → social_media

### Profile DOCX Format

PP profiles contain:
- Key-value pairs in paragraphs: `Name - John Smith`
- Table 0: Relations (Name, Relation, Address, Mobile)
- Table 1: Case Details (FIR, Sections, PS, Brief, Status, Co-accused)

### UO Notes

UO (Under Observation) notes are generated for suspects:
- Based on profile data
- Saved as separate DOCX files
- Named: `1a) UO Name.docx`

---

## Glossary

| Term | Description |
|------|-------------|
| PP | Person Profile (suspect dossier) |
| UO | Under Observation (note) |
| IS | Intelligence Services |
| SSB | Special Branch (Kerala Police) |
| FIR | First Information Report |
| RSU | Regional Security Unit |
| ARFR | Automatic Registry-Filesystem Reconciliation |
| NER | Named Entity Recognition |
| GNN | Graph Neural Network |
| SSE | Server-Sent Events |

---

## Troubleshooting

### Neo4j Connection Issues
```bash
# Check Neo4j is running
curl http://localhost:7474

# Verify credentials
# Default: neo4j/password (or DigitalUniversity in docker)
```

### Qdrant Connection Issues
```bash
# Check Qdrant is running
curl http://localhost:6333/collections

# Check collections exist
```

### Translation Failures
1. Check internet connectivity (for Google Translate fallback)
2. Verify model cache exists for IndicTrans2
3. Check Ollama is running if using Gemma summarization

### Profile Matching Issues
1. Verify PP_DIR path is correct
2. Check PP Form details.docx template exists
3. Review review_registry.json for pending items

---

## License

Internal use only - Kerala Police SSB IS Division
