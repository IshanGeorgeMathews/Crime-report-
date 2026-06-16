# Kerala Police Intelligence Platform (KPIP)

An AI-powered intelligence analysis platform for law enforcement — consolidating daily intelligence reports, building a Neo4j suspect relationship graph, and providing semantic search with LLM-powered Q&A.

---

## Quick Start — Docker (Recommended)

Run the entire stack (backend API, frontend, Neo4j, Qdrant, Ollama) with a single command.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose plugin on Linux)
- At least **8 GB RAM** free for Docker (16 GB recommended when using the LLM)
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/IshanGeorgeMathews/Crime-report-.git
cd "Crime-report-"

# 2. Copy the environment template and set your passwords
cp .env.example .env
# Edit .env — at minimum change NEO4J_PASSWORD and SECRET_KEY

# 3. Build and start all services
docker compose up --build

# 4. Pull an LLM model into Ollama (run in a second terminal after services start)
docker compose exec ollama ollama pull qwen:8b
```

**Access the app:**
| Service | URL |
|---|---|
| 🖥️ Frontend (main app) | http://localhost |
| ⚙️ Backend API | http://localhost:8000/api/v1 |
| 📊 API Docs (Swagger) | http://localhost:8000/api/v1/openapi.json |
| 🗄️ Neo4j Browser | http://localhost:7474 |
| 🔍 Qdrant Dashboard | http://localhost:6333/dashboard |
| 🤖 Ollama | http://localhost:11434 |

**Default login credentials** (seeded on first startup):
| Username | Password | Role |
|---|---|---|
| `admin` | `admin` | Administrator |
| `supervisor` | `supervisor` | Supervisor |
| `analyst` | `analyst` | Analyst |
| `viewer` | `viewer` | Viewer |

> ⚠️ Change default passwords immediately in production via the Admin panel.

### Stopping / Resetting

```bash
# Stop all services (keeps data volumes)
docker compose down

# Stop AND delete all data volumes (full reset)
docker compose down -v
```

---

## Quick Start — Local Development (Python + Node)

For development without Docker.

### Prerequisites
- Python 3.10+ and `pip`
- Node.js 20+ and `npm`
- Neo4j 5.x running locally (download from [neo4j.com](https://neo4j.com/download/))
- Qdrant running locally (optional, for semantic search)
- Ollama running locally (optional, for LLM features)

### Backend

```bash
# 1. Create and activate a virtual environment
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Install root-level dependencies (graph_db, utils, etc.)
cd ..
pip install -r requirements.txt

# 4. Set up environment
cp backend/.env.example backend/.env
# Edit backend/.env — set NEO4J_PASSWORD to your local Neo4j password

# Also set up the root .env (used by graph_db.py CLI scripts)
cp .env.example .env
# Edit .env — set NEO4J_PASSWORD to your local Neo4j password

# 5. Create the Neo4j database
# Open Neo4j Browser at http://localhost:7474
# Run: CREATE DATABASE prosecutorreport
# Or via cypher-shell: cypher-shell -u neo4j -p <password> "CREATE DATABASE prosecutorreport"

# 6. Start the backend API
cd backend
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
# In a new terminal, from the project root
cd frontend
cp .env.example .env
# .env already points to http://localhost:8000/api/v1 — no changes needed for local dev

npm install
npm run dev
# Opens at http://localhost:5173
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose Stack                    │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │   Frontend   │───▶│   Backend    │───▶│    Neo4j      │  │
│  │ React + Nginx│    │  FastAPI     │    │ Graph DB      │  │
│  │   port 80    │    │  port 8000   │    │  port 7687    │  │
│  └──────────────┘    └──────┬───────┘    └───────────────┘  │
│                             │                               │
│                    ┌────────┴────────┐                      │
│                    │                 │                      │
│             ┌──────▼──────┐  ┌──────▼──────┐               │
│             │   Qdrant    │  │   Ollama    │               │
│             │ Vector DB   │  │  LLM Server │               │
│             │  port 6333  │  │ port 11434  │               │
│             └─────────────┘  └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | Technology | Purpose |
|---|---|---|
| Frontend | React 19 + Vite + TypeScript | Web UI |
| Backend API | FastAPI + Python 3.11 | REST API, business logic |
| Graph Database | Neo4j 5 Community | Suspect relationship network |
| Vector Database | Qdrant | Semantic search embeddings |
| LLM | Ollama (qwen:8b) | Summarization, classification, Q&A |
| SQL Database | SQLite (dev) / PostgreSQL (prod) | Users, jobs, reports |

---

## Environment Variables Reference

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|---|---|---|
| `NEO4J_URI` | `bolt://neo4j:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | *(required)* | Neo4j password — **change this** |
| `NEO4J_DATABASE` | `prosecutorreport` | Neo4j database name |
| `SECRET_KEY` | *(required)* | JWT signing secret — **change this** |
| `DATABASE_URL` | SQLite | Use PostgreSQL URL for production |
| `QDRANT_HOST` | `qdrant` | Qdrant hostname |
| `OLLAMA_URL` | `http://ollama:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen:8b` | LLM model name |
| `DISABLE_INDIC_TRANS` | `1` | Set `0` to enable local IndicTrans2 model |
| `PP_DIR` | *(empty)* | Path to PP Form templates folder |
| `BACKEND_CORS_ORIGINS` | localhost origins | Comma-separated allowed CORS origins |

---

## Features

- **Document Consolidation** — Upload daily intelligence `.docx` reports; the system translates (Malayalam→English), classifies, summarizes, and merges them into structured Daily IS Reports
- **Intelligence Graph** — Automatically builds a Neo4j knowledge graph of suspects, crimes, organizations, and cases from consolidated reports. Includes GNN-based link prediction to surface hidden associates
- **Suspect Profiles** — Auto-generated dossiers with activity history, case records, and relationship maps. One-click export to Word (PP Form) and Malayalam UO Note
- **Semantic Search** — Qdrant-powered vector search across all reports and profiles
- **RAG Chat** — Ask natural language questions about intelligence data; answers are grounded in retrieved documents with citations
- **Review Queue** — NER-extracted candidate names are surfaced for supervisor review before being added to the suspect registry
- **Role-Based Access** — Four roles: Admin, Supervisor, Analyst, Viewer

---

## Production Checklist

- [ ] Change `NEO4J_PASSWORD` to a strong password in `.env`
- [ ] Change `SECRET_KEY` to a long random string (`openssl rand -hex 32`)
- [ ] Set `DATABASE_URL` to a PostgreSQL connection string
- [ ] Set `BACKEND_CORS_ORIGINS` to your actual domain
- [ ] Set `DISABLE_INDIC_TRANS=0` if you want local Malayalam translation
- [ ] Configure TLS/HTTPS in front of Nginx (e.g. with Traefik or Caddy)
- [ ] Set up Neo4j database backups
- [ ] Change default user passwords via the Admin panel after first login

---

## Project Structure

```
.
├── docker-compose.yml          # Full stack Docker Compose (start here)
├── Dockerfile.frontend         # Multi-stage Nginx frontend build
├── nginx.conf                  # Nginx SPA + API proxy config
├── .env.example                # Environment variable template
├── .dockerignore
│
├── backend/                    # FastAPI backend
│   ├── Dockerfile
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── api/routes.py
│       ├── services/           # graph_service, rag_service, etc.
│       ├── db/                 # SQLAlchemy models + session
│       └── core/               # Security, paths
│
├── frontend/                   # React + Vite frontend
│   ├── .env.example
│   ├── package.json
│   └── src/
│       ├── features/           # Page components
│       ├── hooks/              # React Query hooks
│       ├── lib/api.ts          # Axios API client
│       └── stores/             # Zustand state stores
│
├── graph_db.py                 # Neo4j GraphDatabase wrapper + GNN
├── utils.py                    # Document processing utilities
├── ner_engine.py               # BERT NER engine
├── translation.py              # Malayalam translation engine
└── requirements.txt            # Root-level Python dependencies
```

---

## Troubleshooting

**Graph shows no data after startup**
- Neo4j takes ~60 seconds to start. The API waits for it (healthcheck), but allow a minute before loading the graph page.
- The `prosecutorreport` database must exist. Neo4j Community creates a default database; you need to create the named database: in the Neo4j Browser run `CREATE DATABASE prosecutorreport`.

**Ollama model not responding**
- After `docker compose up`, pull the model: `docker compose exec ollama ollama pull qwen:8b`
- This downloads ~4 GB, wait for it to complete before using LLM features.

**"Permission denied" on uploads**
- The uploads volume is managed by Docker. If you see permission errors, run: `docker compose down -v && docker compose up --build`

**Frontend can't reach the API**
- In Docker mode, the frontend Nginx proxies `/api` to the `api` container — no CORS issues.
- In local dev mode, ensure `VITE_API_URL=http://localhost:8000/api/v1` in `frontend/.env` and the backend is running.
