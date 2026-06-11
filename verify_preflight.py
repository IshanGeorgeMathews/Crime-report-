"""
=============================================================
  KPIP - Pre-Consolidation Preflight Verification Script
=============================================================
Run this from the project root (Digital University Project/Code):
  python verify_preflight.py

Checks every dependency the consolidation pipeline needs before
you run it, and gives a clear PASS / WARN / FAIL report.
"""
import io, sys
# Force UTF-8 output so unicode characters print cleanly on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sys
import os
import socket
import importlib
import subprocess
import json
from pathlib import Path

# ── colour helpers ──────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"

def ok(msg):    print(f"  {GREEN}[PASS]{RESET}  {msg}")
def warn(msg):  print(f"  {YELLOW}[WARN]{RESET}  {msg}")
def fail(msg):  print(f"  {RED}[FAIL]{RESET}  {msg}")
def info(msg):  print(f"  {CYAN}[INFO]{RESET}  {msg}")
def header(msg):
    print(f"\n{BOLD}{CYAN}{'-'*58}{RESET}")
    print(f"{BOLD}{CYAN}  {msg}{RESET}")
    print(f"{BOLD}{CYAN}{'-'*58}{RESET}")

# ── counters ─────────────────────────────────────────────────
PASSES = 0
WARNS  = 0
FAILS  = 0

def check(condition, pass_msg, fail_msg, critical=True):
    global PASSES, WARNS, FAILS
    if condition:
        ok(pass_msg)
        PASSES += 1
        return True
    else:
        if critical:
            fail(fail_msg)
            FAILS += 1
        else:
            warn(fail_msg)
            WARNS += 1
        return False

def tcp_reachable(host, port, timeout=2.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def http_get(url, timeout=4):
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, r.read().decode()
    except Exception as e:
        return None, str(e)

# ═══════════════════════════════════════════════════════════
# Determine project root (this file lives in Code/)
# ═══════════════════════════════════════════════════════════
ROOT = Path(__file__).resolve().parent          # …/Code
BACKEND = ROOT / "backend"
BACKEND_APP = BACKEND / "app"

# ═══════════════════════════════════════════════════════════
print(f"\n{BOLD}{'='*58}")
print("  KPIP Pre-Consolidation Preflight Check")
print(f"{'='*58}{RESET}")
print(f"  Root : {ROOT}")
print(f"  Time : {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ───────────────────────────────────────────────────────────
header("1 · Python Environment")
# ───────────────────────────────────────────────────────────

py_ver = sys.version_info
check(
    py_ver >= (3, 10),
    f"Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}",
    f"Python ≥3.10 required (found {py_ver.major}.{py_ver.minor}.{py_ver.micro})"
)

# Are we inside the venv?
in_venv = (
    hasattr(sys, "real_prefix") or
    (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
)
check(in_venv, "Running inside virtualenv", "Not in a virtualenv — activate backend/venv first", critical=False)

# ───────────────────────────────────────────────────────────
header("2 · Required Python Packages")
# ───────────────────────────────────────────────────────────

PACKAGES = [
    # (import_name, display_name, critical)
    ("fastapi",              "fastapi",              True),
    ("uvicorn",              "uvicorn",              True),
    ("pydantic",             "pydantic ≥2",          True),
    ("pydantic_settings",    "pydantic-settings",    True),
    ("sqlalchemy",           "SQLAlchemy ≥2",        True),
    ("aiosqlite",            "aiosqlite",            True),
    ("asyncpg",              "asyncpg",              True),
    ("alembic",              "alembic",              True),
    ("passlib",              "passlib[bcrypt]",      True),
    ("bcrypt",               "bcrypt",               True),
    ("jose",                 "python-jose",          True),
    ("multipart",            "python-multipart",     True),
    ("httpx",                "httpx",                True),
    ("docx",                 "python-docx",          True),
    ("deep_translator",      "deep-translator",      True),
    ("qdrant_client",        "qdrant-client",        False),
    ("sentence_transformers","sentence-transformers",False),
    ("neo4j",                "neo4j",                False),
    ("sse_starlette",        "sse-starlette",        True),
    ("structlog",            "structlog",            True),
    ("dotenv",               "python-dotenv",        True),
    ("requests",             "requests",             True),
]

for import_name, display, critical in PACKAGES:
    try:
        importlib.import_module(import_name)
        ok(f"{display}")
        PASSES += 1
    except ImportError:
        if critical:
            fail(f"{display}  ← pip install {display}")
            FAILS += 1
        else:
            warn(f"{display}  ← optional, needed for full pipeline")
            WARNS += 1

# ───────────────────────────────────────────────────────────
header("3 · Root-Level Module Imports (utils / intel_tool / graph_db)")
# ───────────────────────────────────────────────────────────

# Add root to path so we can import utils, intel_tool etc.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ROOT_MODULES = {
    "utils": [
        "read_docx_paragraphs", "is_malayalam", "translate_ml_to_en",
        "extract_district_tag", "build_daily_report",
        "build_less_priority_report", "DISTRICT_CODES",
        "SOCIAL_MEDIA_KEYWORDS", "extract_details_from_docx_paragraphs",
    ],
    "intel_tool": [
        "_classify_and_summarize_item",
        "_sync_profiles_from_texts",
        "_resolve_ollama_model",
    ],
    "graph_db": [],     # just import
    "ner_engine": [],
    "translation": [],
}

for mod_name, symbols in ROOT_MODULES.items():
    try:
        mod = importlib.import_module(mod_name)
        ok(f"import {mod_name}")
        PASSES += 1
        for sym in symbols:
            if hasattr(mod, sym):
                ok(f"  └─ {mod_name}.{sym}")
                PASSES += 1
            else:
                fail(f"  └─ {mod_name}.{sym}  ← MISSING in module!")
                FAILS += 1
    except ImportError as e:
        fail(f"import {mod_name}  ← {e}")
        FAILS += 1

# ───────────────────────────────────────────────────────────
header("4 · Backend App Imports")
# ───────────────────────────────────────────────────────────

BACKEND_IMPORTS = [
    "app.config",
    "app.core.security",
    "app.core.paths",
    "app.db.session",
    "app.db.models",
    "app.api.routes",
    "app.services.consolidation_service",
    "app.services.qdrant_service",
    "app.services.profile_service",
    "app.services.graph_service",
    "app.services.ner_service",
    "app.services.llm_service",
    "app.services.translation_service",
]

# Add backend dir to path as uvicorn does
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

for mod_path in BACKEND_IMPORTS:
    try:
        importlib.import_module(mod_path)
        ok(f"import {mod_path}")
        PASSES += 1
    except Exception as e:
        fail(f"import {mod_path}  ← {e}")
        FAILS += 1

# ───────────────────────────────────────────────────────────
header("5 · .env File & Critical Config Keys")
# ───────────────────────────────────────────────────────────

env_file = BACKEND / ".env"
check(env_file.exists(), f".env found at {env_file}", f".env missing at {env_file}")

if env_file.exists():
    env_content = env_file.read_text(encoding="utf-8")
    REQUIRED_ENV_KEYS = [
        "SECRET_KEY", "DATABASE_URL",
        "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD",
        "QDRANT_HOST", "QDRANT_PORT",
        "OLLAMA_URL", "OLLAMA_MODEL",
    ]
    for key in REQUIRED_ENV_KEYS:
        check(
            key in env_content,
            f"{key} defined in .env",
            f"{key} NOT found in .env"
        )

# ───────────────────────────────────────────────────────────
header("6 · Directory Structure")
# ───────────────────────────────────────────────────────────

# Try to load settings for directory paths
try:
    from app.config import settings
    PP_DIR       = Path(settings.PP_DIR)
    UPLOAD_DIR   = Path(settings.UPLOAD_DIR)
    DAILY_DIR    = PP_DIR.parent / "DAILY IS REPORT"
    LESS_DIR     = PP_DIR.parent / "Daily less priority report"
except Exception as e:
    warn(f"Could not load app.config.settings to check dirs: {e}")
    PP_DIR = UPLOAD_DIR = DAILY_DIR = LESS_DIR = None

DIRS_TO_CHECK = {
    "backend/uploads"         : BACKEND / "uploads",
    "PP & Uo Note Dummy dir"  : PP_DIR,
    "DAILY IS REPORT dir"     : DAILY_DIR,
    "Daily less priority dir" : LESS_DIR,
}

for label, dpath in DIRS_TO_CHECK.items():
    if dpath is None:
        warn(f"{label}  ← could not resolve path (settings load failed)")
        WARNS += 1
        continue
    if dpath.exists():
        ok(f"{label} → {dpath}")
        PASSES += 1
    else:
        # Non-critical: can be created at runtime
        warn(f"{label} missing → {dpath}  (will be auto-created if needed)")
        WARNS += 1

# PP Template
if PP_DIR:
    pp_template = Path(settings.PP_TEMPLATE)
    check(
        pp_template.exists(),
        f"PP Form template exists → {pp_template.name}",
        f"PP Form template MISSING → {pp_template}",
        critical=False
    )

# ───────────────────────────────────────────────────────────
header("7 · SQLite Database (Local Dev)")
# ───────────────────────────────────────────────────────────

sqlite_path = BACKEND / "kpip.db"
if sqlite_path.exists():
    size_kb = sqlite_path.stat().st_size // 1024
    ok(f"kpip.db exists ({size_kb} KB)")
    PASSES += 1
    # Try opening it
    try:
        import sqlite3
        con = sqlite3.connect(str(sqlite_path))
        tables = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        con.close()
        table_names = [t[0] for t in tables]
        ok(f"SQLite readable — tables: {', '.join(table_names) or '(empty)'}")
        PASSES += 1
        # Check for required tables
        for tbl in ["users", "jobs", "job_events", "reports", "report_items"]:
            check(
                tbl in table_names,
                f"Table '{tbl}' exists",
                f"Table '{tbl}' MISSING — run the backend once to auto-create",
                critical=False
            )
    except Exception as e:
        fail(f"Could not open kpip.db: {e}")
        FAILS += 1
else:
    warn("kpip.db not found — it will be created on first backend startup")
    WARNS += 1

# ───────────────────────────────────────────────────────────
header("8 · Network Services")
# ───────────────────────────────────────────────────────────

SERVICES = [
    ("FastAPI Backend",  "localhost", 8000, True,  "http://localhost:8000/api/v1/"),
    ("Neo4j Bolt",       "localhost", 7687, False, None),
    ("Qdrant REST",      "localhost", 6333, False, "http://localhost:6333/"),
    ("Ollama",           "localhost", 11434,False, "http://localhost:11434/api/tags"),
]

for svc_name, host, port, critical, health_url in SERVICES:
    reachable = tcp_reachable(host, port)
    if reachable:
        ok(f"{svc_name} reachable at {host}:{port}")
        PASSES += 1
        if health_url:
            status, body = http_get(health_url)
            if status and status < 400:
                ok(f"  └─ Health check {health_url}  →  HTTP {status}")
                PASSES += 1
            else:
                warn(f"  └─ Health check failed for {health_url}: {body[:80]}")
                WARNS += 1
    else:
        msg = f"{svc_name} NOT reachable at {host}:{port}"
        if critical:
            fail(msg + "  ← backend MUST be running")
            FAILS += 1
        else:
            warn(msg + "  ← optional service, pipeline will skip gracefully")
            WARNS += 1

# ── Ollama model check ────────────────────────────────────
if tcp_reachable("localhost", 11434):
    try:
        status, body = http_get("http://localhost:11434/api/tags")
        if status == 200:
            data = json.loads(body)
            models = [m["name"] for m in data.get("models", [])]
            if models:
                ok(f"Ollama models available: {', '.join(models)}")
                PASSES += 1
                # Check for the configured model
                try:
                    from app.config import settings as s
                    wanted = s.OLLAMA_MODEL
                    found = any(wanted in m for m in models)
                    check(
                        found,
                        f"Configured model '{wanted}' present",
                        f"Configured model '{wanted}' NOT found in Ollama  ← ollama pull {wanted}",
                        critical=False
                    )
                except Exception:
                    pass
            else:
                warn("Ollama reachable but no models loaded  ← ollama pull gemma2:9b")
                WARNS += 1
    except Exception as e:
        warn(f"Ollama model list check failed: {e}")
        WARNS += 1

# ───────────────────────────────────────────────────────────
header("9 · FastAPI Endpoint Smoke Tests")
# ───────────────────────────────────────────────────────────

if tcp_reachable("localhost", 8000):
    ENDPOINTS = [
        ("/api/v1/openapi.json", "OpenAPI schema / health"),
    ]
    for path, label in ENDPOINTS:
        status, body = http_get(f"http://localhost:8000{path}")
        if status and status < 400:
            ok(f"{label}  →  HTTP {status}")
            PASSES += 1
        else:
            fail(f"{label}  →  HTTP {status}  ({body[:60]})")
            FAILS += 1

    # Auth smoke-test (login)
    try:
        import urllib.request, urllib.parse, urllib.error
        login_payload = json.dumps({
            "username": "admin", "password": "admin"
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp_body = json.loads(resp.read().decode())
            token = resp_body.get("data", {}).get("token", "")
            if token:
                ok("Auth /login (admin)  →  JWT received")
                PASSES += 1
            else:
                warn("Auth /login returned 200 but no token in body")
                WARNS += 1
    except urllib.error.HTTPError as e:
        if e.code == 401:
            warn("Auth /login  →  401 (admin user may not be seeded yet)")
            WARNS += 1
        else:
            fail(f"Auth /login  →  HTTP {e.code}")
            FAILS += 1
    except Exception as e:
        warn(f"Auth /login smoke test skipped: {e}")
        WARNS += 1
else:
    warn("Backend not running — skipping endpoint smoke tests")
    WARNS += 1

# ───────────────────────────────────────────────────────────
header("10 · Consolidation Pipeline Self-Check")
# ───────────────────────────────────────────────────────────

# Check that all functions used in consolidation_service.py are importable
CONSOL_DEPS = {
    "utils": ["read_docx_paragraphs","is_malayalam","translate_ml_to_en",
               "extract_district_tag","build_daily_report",
               "build_less_priority_report","DISTRICT_CODES",
               "SOCIAL_MEDIA_KEYWORDS","extract_details_from_docx_paragraphs"],
    "intel_tool": ["_classify_and_summarize_item",
                   "_sync_profiles_from_texts","_resolve_ollama_model"],
}

for mod_name, syms in CONSOL_DEPS.items():
    try:
        mod = sys.modules.get(mod_name) or importlib.import_module(mod_name)
        missing = [s for s in syms if not hasattr(mod, s)]
        if not missing:
            ok(f"{mod_name}: all {len(syms)} required symbols present")
            PASSES += 1
        else:
            fail(f"{mod_name}: MISSING symbols → {', '.join(missing)}")
            FAILS += 1
    except Exception as e:
        fail(f"{mod_name}: import error → {e}")
        FAILS += 1

# Verify python-docx Document class works
try:
    from docx import Document as _Doc
    ok("python-docx Document class importable")
    PASSES += 1
except Exception as e:
    fail(f"python-docx Document import failed: {e}")
    FAILS += 1

# ───────────────────────────────────────────────────────────
header("11 · Upload Folder Write Permissions")
# ───────────────────────────────────────────────────────────

upload_dir = BACKEND / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)
test_file  = upload_dir / "_preflight_write_test.tmp"
try:
    test_file.write_text("ok")
    test_file.unlink()
    ok(f"backend/uploads is writable")
    PASSES += 1
except Exception as e:
    fail(f"backend/uploads NOT writable: {e}")
    FAILS += 1

# ═══════════════════════════════════════════════════════════
print(f"\n{BOLD}{'='*58}")
print("  SUMMARY")
print(f"{'='*58}{RESET}")
print(f"  {GREEN}PASS{RESET}  {PASSES}")
print(f"  {YELLOW}WARN{RESET}  {WARNS}   <- optional / gracefully skipped by pipeline")
print(f"  {RED}FAIL{RESET}  {FAILS}   <- must fix before consolidation")
print(f"{BOLD}{'='*58}{RESET}\n")

if FAILS == 0 and WARNS == 0:
    print(f"{GREEN}{BOLD}  [OK] ALL CHECKS PASSED - Safe to run consolidation!{RESET}\n")
elif FAILS == 0:
    print(f"{YELLOW}{BOLD}  [OK] No critical failures - consolidation can run.")
    print(f"  Warnings indicate optional services (Neo4j/Qdrant/Ollama)")
    print(f"  that are offline; the pipeline will skip those steps.{RESET}\n")
else:
    print(f"{RED}{BOLD}  [!!] {FAILS} CRITICAL FAILURE(S) - fix before running consolidation!{RESET}\n")

sys.exit(0 if FAILS == 0 else 1)
