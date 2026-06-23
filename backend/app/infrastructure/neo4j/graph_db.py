"""
graph_db.py - Neo4j Graph Database & GNN Module for Intelligence Relations
==========================================================================
Implements:
  - Neo4j-backed graph database for representing relationships between:
      * Records  ( consolidated reports )
      * Crimes   ( specific event details )
      * Individuals ( suspects / persons of interest )
      * Organizations
      * Cases
  - TF-IDF feature extraction for nodes using scikit-learn.
  - Native PyTorch-based Graph Convolutional Network (GCN) for node embeddings.
  - Link prediction training and similarity-based name disambiguation.

Neo4j connection: bolt://127.0.0.1:7687  database: prosecutorreport
"""

import os
import json
import math
from datetime import datetime, date
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from neo4j import GraphDatabase as Neo4jDriver

# ---------------------------------------------------------------------------
# Import Name-validation helper from app.infrastructure.documents.utils
# ---------------------------------------------------------------------------
from app.infrastructure.documents.utils import _is_valid_person_name, is_fuzzy_match, soundex_kerala

# ---------------------------------------------------------------------------
# Load local configuration from environment variables
# ---------------------------------------------------------------------------
def load_env(filepath=".env"):
    """Load variables from .env file into os.environ.

    Variables already present in the environment (e.g. set by Docker or the
    shell) take priority and are NOT overwritten.  This makes the module safe
    to import inside a Docker container where env vars are injected at runtime.
    """
    if not os.path.isabs(filepath):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(base_dir, filepath)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    # Only set if not already defined in the environment
                    os.environ.setdefault(key, val)

load_env()



def _parse_date(value: str):
    """Parse KPIP date formats into a date object."""
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            continue
    return None


def _format_date(value):
    """Normalize a date/date-string to ISO format."""
    if isinstance(value, date):
        return value.isoformat()
    parsed = _parse_date(value)
    return parsed.isoformat() if parsed else ""

# ---------------------------------------------------------------------------
# Default Neo4j connection settings
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "prosecutorreport")
NEO4J_AUTH = (NEO4J_USER, NEO4J_PASSWORD)


class Neo4jTransactionContext:
    def __init__(self, db):
        self.db = db
        self.session = None
        self.tx = None

    def __enter__(self):
        self.session = self.db._driver.session(database=self.db.database)
        self.tx = self.session.begin_transaction()
        self.db._current_tx = self.tx
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.tx.rollback()
            else:
                self.tx.commit()
        except Exception as e:
            print(f"[Warning] Failed to commit transaction: {e}")
            try:
                self.tx.rollback()
            except Exception:
                pass
        finally:
            self.tx.close()
            self.session.close()
            self.db._current_tx = None


class GraphDatabase:

    def __init__(
        self,
        uri: str = NEO4J_URI,
        auth: tuple = NEO4J_AUTH,
        database: str = NEO4J_DATABASE,
    ):
        self.uri = uri
        self.auth = auth
        self.database = database
        self._driver = Neo4jDriver.driver(uri, auth=auth)
        self._current_tx = None
        # Audit log location — kept in the project Code directory
        self._audit_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "graph_db_audit.jsonl"
        )
        try:
            self._driver.verify_connectivity()
            print(f"[Info] Connected to Neo4j at {uri}, database='{database}'.")
            try:
                from scripts.migration import db_migrations
                db_migrations.ensure_indexes()
            except ImportError:
                try:
                    import db_migrations
                    db_migrations.ensure_indexes()
                except Exception as migration_error:
                    print(f"[Warning] Index migrations failed: {migration_error}")
            except Exception as migration_error:
                print(f"[Warning] Index migrations failed: {migration_error}")
        except Exception as e:
            print(f"[Error] Failed to connect to Neo4j at {uri}: {e}")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the Neo4j driver connection."""
        if self._driver:
            self._driver.close()

    # ------------------------------------------------------------------
    # Compatibility stubs — Neo4j writes are immediate, no load/save
    # ------------------------------------------------------------------
    def load(self):
        """No-op — Neo4j is always loaded."""
        pass

    def save(self):
        """No-op — Neo4j writes are transactional and immediate."""
        pass

    # ------------------------------------------------------------------
    # Transaction Batching Context Manager
    # ------------------------------------------------------------------
    def transaction(self):
        """Return a context manager to run multiple queries in a single transaction."""
        return Neo4jTransactionContext(self)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _run(self, query: str, **params):
        """Execute a Cypher query and return a list of record dicts."""
        try:
            if self._current_tx is not None:
                result = self._current_tx.run(query, **params)
                return [record.data() for record in result]
            with self._driver.session(database=self.database) as session:
                result = session.run(query, **params)
                return [record.data() for record in result]
        except Exception as e:
            print(f"[Warning] Neo4j query execution failed: {e}")
            return []

    def _run_single(self, query: str, **params):
        """Execute a Cypher query and return a single record dict or None."""
        try:
            if self._current_tx is not None:
                result = self._current_tx.run(query, **params)
                record = result.single()
                return record.data() if record else None
            with self._driver.session(database=self.database) as session:
                result = session.run(query, **params)
                record = result.single()
                return record.data() if record else None
        except Exception as e:
            print(f"[Warning] Neo4j single query execution failed: {e}")
            return None

    def _log_audit(self, action: str, details: dict):
        """Append a single-line JSON entry to the audit log (JSONL format).

        This is O(1) per call — no file parsing, no array management.
        Safe for concurrent writes via filelock.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "details": details,
        }
        try:
            from filelock import FileLock
            lock = FileLock(self._audit_path + ".lock", timeout=5)
            with lock:
                with open(self._audit_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except ImportError:
            # Fallback without locking if filelock not installed
            try:
                with open(self._audit_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            except Exception as e:
                print(f"[Warning] Failed to write to audit log: {e}")
        except Exception as e:
            print(f"[Warning] Failed to write to audit log: {e}")

    # ------------------------------------------------------------------
    # Node creation / update
    # ------------------------------------------------------------------
    def add_individual(
        self,
        name: str,
        pp_id: str = "",
        ps: str = "",
        address: str = "",
        activity_type: str = "",
        canonical_node_id: str = "",
    ):
        """Add or update an Individual node.

        Returns the node_id string on success, or None if *name* fails the
        _is_valid_person_name() validation.

        If *canonical_node_id* is provided (e.g. derived from a PP-ID or the
        profile's full canonical name), it is used instead of deriving the
        node-id from *name*.  This prevents duplicate nodes when a report text
        mentions a short alias (e.g. "Sachin") but the canonical profile name
        is longer (e.g. "Sachin Divakaran").

        On MATCH the existing ``n.name`` is preserved: the name is only set
        when the node is first created, so a later mention with a shorter
        or different name variant does **not** overwrite the original.
        """
        if not _is_valid_person_name(name):
            return None

        node_id = canonical_node_id or f"ind_{name.lower().replace(' ', '_')}"
        description = (
            f"Individual name: {name}. PP ID: {pp_id or 'None'}. "
            f"Police Station: {ps or 'None'}. Address: {address or 'None'}. "
            f"Type of Activity: {activity_type or 'None'}."
        )

        self._run(
            """
            MERGE (n:Individual {node_id: $nid})
            ON CREATE SET
                n.type        = 'individual',
                n.name        = $name,
                n.pp_id       = $pp_id,
                n.police_station = $ps,
                n.address     = $address,
                n.activity_type = $activity_type,
                n.description = $description
            ON MATCH SET
                n.name        = CASE WHEN n.name IS NULL OR n.name = '' THEN $name ELSE n.name END,
                n.pp_id       = CASE WHEN $pp_id <> '' THEN $pp_id       ELSE n.pp_id END,
                n.police_station = CASE WHEN $ps <> '' THEN $ps         ELSE n.police_station END,
                n.address     = CASE WHEN $address <> '' THEN $address   ELSE n.address END,
                n.activity_type = CASE WHEN $activity_type <> '' THEN $activity_type ELSE n.activity_type END,
                n.description = CASE WHEN n.name IS NULL OR n.name = '' THEN $description ELSE n.description END
            """,
            nid=node_id,
            name=name,
            pp_id=pp_id,
            ps=ps,
            address=address,
            activity_type=activity_type,
            description=description,
        )
        self._log_audit("add_individual", {"node_id": node_id, "name": name, "pp_id": pp_id})
        return node_id

    def add_record(self, date_str: str, filepath: str = ""):
        """Add or update a Record node."""
        node_id = f"rec_{date_str.replace('.', '_')}"
        description = f"Intelligence Record consolidated for date {date_str}. File path: {filepath}."
        self._run(
            """
            MERGE (n:Record {node_id: $nid})
            SET n.type = 'record',
                n.date = $date_str,
                n.filepath = $filepath,
                n.description = $description
            """,
            nid=node_id,
            date_str=date_str,
            filepath=filepath,
            description=description,
        )
        self._log_audit("add_record", {"node_id": node_id, "date": date_str, "filepath": filepath})
        return node_id

    def add_crime(self, crime_id: str, text: str, district: str = "", category: str = "", date_str: str = ""):
        """Add or update a Crime/Event node."""
        node_id = f"cri_{crime_id}"
        description = (
            f"Crime Event: {text[:200]}... District: {district}. "
            f"Category: {category}. Date: {date_str}."
        )
        self._run(
            """
            MERGE (n:Crime {node_id: $nid})
            SET n.type = 'crime',
                n.text = $text,
                n.district = $district,
                n.category = $category,
                n.date = $date_str,
                n.description = $description
            """,
            nid=node_id,
            text=text,
            district=district,
            category=category,
            date_str=date_str,
            description=description,
        )
        self._log_audit("add_crime", {"node_id": node_id, "district": district, "date": date_str})
        return node_id

    def add_protest(
        self,
        protest_id: str,
        text: str,
        district: str = "",
        category: str = "",
        date_str: str = "",
        organizer: str = ""
    ):
        """Add or update a Protest/Non-Crime node in the Neo4j database."""
        node_id = f"prt_{protest_id}"
        description = f"Protest/Event: {text[:100]}... Type: {category or 'Protest'}. Date: {date_str}. Organizer: {organizer or 'None'}."
        
        self._run(
            """
            MERGE (n:Protest {node_id: $nid})
            SET n.type        = 'protest',
                n.text        = $text,
                n.district    = $district,
                n.category    = $category,
                n.date        = $date,
                n.organizer   = $organizer,
                n.description = $description
            """,
            nid=node_id,
            text=text,
            district=district,
            category=category,
            date=date_str,
            organizer=organizer,
            description=description,
        )
        self._log_audit("add_protest", {"node_id": node_id, "district": district, "date": date_str})
        return node_id

    def add_organization(self, org_name: str, remarks: str = ""):
        """Add or update an Organization node."""
        if not org_name or len(org_name.strip()) < 2:
            return None
        node_id = f"org_{org_name.lower().replace(' ', '_').replace('/', '_')}"
        description = f"Organization: {org_name}. Remarks: {remarks or 'None'}."
        self._run(
            """
            MERGE (n:Organization {node_id: $nid})
            ON CREATE SET
                n.type = 'organization',
                n.name = $org_name,
                n.remarks = $remarks,
                n.description = $description
            ON MATCH SET
                n.remarks = CASE WHEN $remarks <> '' THEN $remarks ELSE n.remarks END,
                n.description = $description
            """,
            nid=node_id,
            org_name=org_name,
            remarks=remarks,
            description=description,
        )
        self._log_audit("add_organization", {"node_id": node_id, "name": org_name})
        return node_id

    def add_case(self, case_id: str, fir: str = "", sections: str = "", ps: str = "", brief: str = ""):
        """Add or update a Case node."""
        if not case_id:
            return None
        node_id = f"case_{case_id.lower().replace(' ', '_').replace('/', '_')}"
        description = (
            f"Case FIR: {fir or 'None'}. Sections: {sections or 'None'}. "
            f"Police Station: {ps or 'None'}. Brief: {brief or 'None'}."
        )
        self._run(
            """
            MERGE (n:Case {node_id: $nid})
            ON CREATE SET
                n.type = 'case',
                n.fir_number = $fir,
                n.under_sections = $sections,
                n.police_station = $ps,
                n.case_brief = $brief,
                n.description = $description
            ON MATCH SET
                n.fir_number = CASE WHEN $fir <> '' THEN $fir ELSE n.fir_number END,
                n.under_sections = CASE WHEN $sections <> '' THEN $sections ELSE n.under_sections END,
                n.police_station = CASE WHEN $ps <> '' THEN $ps ELSE n.police_station END,
                n.case_brief = CASE WHEN $brief <> '' THEN $brief ELSE n.case_brief END,
                n.description = $description
            """,
            nid=node_id,
            fir=fir,
            sections=sections,
            ps=ps,
            brief=brief,
            description=description,
        )
        self._log_audit("add_case", {"node_id": node_id, "fir_number": fir})
        return node_id

    def merge_individuals(self, keep_id: str, delete_id: str):
        """Merge two individual nodes, redirecting all relationships of delete_id to keep_id,
        and then deleting the duplicate delete_id node.
        """
        # 1. Redirect all relationships originating from or targeting delete_id to keep_id
        self._run(
            """
            MATCH (d:Individual {node_id: $delete_id})-[r]->(target)
            MATCH (k:Individual {node_id: $keep_id})
            MERGE (k)-[new_r:TYPE(r)]->(target)
            ON CREATE SET new_r = r
            DELETE r
            """,
            keep_id=keep_id,
            delete_id=delete_id
        )
        self._run(
            """
            MATCH (source)-[r]->(d:Individual {node_id: $delete_id})
            MATCH (k:Individual {node_id: $keep_id})
            MERGE (source)-[new_r:TYPE(r)]->(k)
            ON CREATE SET new_r = r
            DELETE r
            """,
            keep_id=keep_id,
            delete_id=delete_id
        )
        # 2. Delete the delete_id node
        self._run(
            "MATCH (d:Individual {node_id: $delete_id}) DETACH DELETE d",
            delete_id=delete_id
        )
        self._log_audit("merge_individuals", {"keep_id": keep_id, "delete_id": delete_id})

    # ------------------------------------------------------------------
    # Relationship creation / update
    # ------------------------------------------------------------------
    def add_relation(
        self,
        u_id: str,
        v_id: str,
        rel_type: str,
        weight: float = 1.0,
        report_date: str = "",
        decay_half_life_days: float = 60.0,
    ):
        """Add or update a relationship between two nodes with temporal decay metadata."""
        # First get both node types
        rec = self._run_single(
            """
            OPTIONAL MATCH (a {node_id: $uid})
            OPTIONAL MATCH (b {node_id: $vid})
            RETURN a.type AS type_u, b.type AS type_v
            """,
            uid=u_id,
            vid=v_id,
        )
        if not rec or not rec.get("type_u") or not rec.get("type_v"):
            return

        type_u = rec["type_u"]
        type_v = rec["type_v"]

        # Enforce structural type constraints
        valid_rels = {
            ("individual", "crime"): {"ASSOCIATED_WITH"},
            ("crime", "individual"): {"ASSOCIATED_WITH"},
            ("individual", "protest"): {"PARTICIPATED_IN", "ASSOCIATED_WITH"},
            ("protest", "individual"): {"PARTICIPATED_IN", "ASSOCIATED_WITH"},
            ("individual", "record"): {"MENTIONED_IN"},
            ("record", "individual"): {"MENTIONED_IN"},
            ("individual", "individual"): {"CO_OCCURRED_WITH"},
            ("crime", "record"): {"REPORTED_IN"},
            ("record", "crime"): {"REPORTED_IN"},
            ("protest", "record"): {"REPORTED_IN"},
            ("record", "protest"): {"REPORTED_IN"},
            ("individual", "organization"): {"MEMBER_OF"},
            ("organization", "individual"): {"MEMBER_OF"},
            ("individual", "case"): {"ACCUSED_IN"},
            ("case", "individual"): {"ACCUSED_IN"},
        }

        pair = (type_u, type_v)
        if pair not in valid_rels or rel_type not in valid_rels[pair]:
            print(f"[Warning] Rejecting invalid relation: {u_id} ({type_u}) -[{rel_type}]-> {v_id} ({type_v})")
            return

        existing = self._run_single(
            f"""
            MATCH (a {{node_id: $uid}}), (b {{node_id: $vid}})
            OPTIONAL MATCH (a)-[r:{rel_type}]-(b)
            RETURN properties(r) AS props
            """,
            uid=u_id,
            vid=v_id,
        )
        props = (existing or {}).get("props") or {}

        event_date = _parse_date(report_date)
        stored_last_seen = _parse_date(props.get("last_seen"))
        lambda_decay = math.log(2.0) / max(float(decay_half_life_days or 60.0), 1.0)

        previous_weight = float(props.get("weight") or 0.0)
        if props and event_date and stored_last_seen:
            elapsed_days = max((event_date - stored_last_seen).days, 0)
            previous_weight *= math.exp(-lambda_decay * elapsed_days)

        new_weight = previous_weight + float(weight)
        new_base_weight = float(props.get("base_weight") or 0.0) + float(weight)
        new_occurrence_count = int(props.get("occurrence_count") or 0) + 1

        first_seen_date = _parse_date(props.get("first_seen")) or event_date
        last_seen_date = stored_last_seen or event_date
        if event_date and first_seen_date:
            first_seen_date = min(first_seen_date, event_date)
        elif event_date:
            first_seen_date = event_date
        if event_date and last_seen_date:
            last_seen_date = max(last_seen_date, event_date)
        elif event_date:
            last_seen_date = event_date

        query = f"""
            MATCH (a {{node_id: $uid}}), (b {{node_id: $vid}})
            MERGE (a)-[r:{rel_type}]-(b)
            SET r.type = $rel_type,
                r.weight = $new_weight,
                r.base_weight = $base_weight,
                r.occurrence_count = $occurrence_count,
                r.first_seen = CASE WHEN $first_seen <> '' THEN $first_seen ELSE r.first_seen END,
                r.last_seen = CASE WHEN $last_seen <> '' THEN $last_seen ELSE r.last_seen END,
                r.decay_half_life_days = $decay_half_life_days,
                r.last_reported_at = CASE WHEN $last_seen <> '' THEN $last_seen ELSE r.last_reported_at END
            RETURN properties(r) AS props
        """
        result = self._run_single(
            query,
            uid=u_id,
            vid=v_id,
            rel_type=rel_type,
            new_weight=new_weight,
            base_weight=new_base_weight,
            occurrence_count=new_occurrence_count,
            first_seen=_format_date(first_seen_date),
            last_seen=_format_date(last_seen_date),
            decay_half_life_days=float(decay_half_life_days or 60.0),
        )
        if result:
            self._log_audit(
                "add_relation",
                {
                    "u_id": u_id,
                    "v_id": v_id,
                    "rel_type": rel_type,
                    "weight": new_weight,
                    "report_date": report_date,
                    "occurrence_count": new_occurrence_count,
                },
            )

    # ------------------------------------------------------------------
    # Query helpers  (replace direct db.G.* access in intel_tool.py)
    # ------------------------------------------------------------------
    def has_node(self, node_id: str) -> bool:
        """Check if a node with the given node_id exists."""
        rec = self._run_single(
            "MATCH (n {node_id: $nid}) RETURN count(n) AS cnt",
            nid=node_id,
        )
        return rec is not None and rec.get("cnt", 0) > 0

    def get_node(self, node_id: str) -> dict:
        """Return all properties of a node as a dict. Returns {} if not found."""
        rec = self._run_single(
            "MATCH (n {node_id: $nid}) RETURN properties(n) AS props",
            nid=node_id,
        )
        return rec["props"] if rec and rec.get("props") else {}

    def set_node_property(self, node_id: str, key: str, value):
        """Set a single property on a node."""
        import re
        if not re.match(r"^[a-zA-Z0-9_]+$", key):
            raise ValueError(f"Invalid Cypher property key: {key}")
        # Use a safe parameterized approach
        self._run(
            f"MATCH (n {{node_id: $nid}}) SET n.`{key}` = $val",
            nid=node_id,
            val=value,
        )

    def neighbors(self, node_id: str) -> list:
        """Return a list of neighbor node_ids."""
        records = self._run(
            """
            MATCH (n {node_id: $nid})-[r]-(m)
            RETURN m.node_id AS neighbor_id
            """,
            nid=node_id,
        )
        return [r["neighbor_id"] for r in records if r.get("neighbor_id")]

    def get_edge(self, u_id: str, v_id: str) -> dict:
        """Return edge properties between two nodes. Returns {} if no edge."""
        rec = self._run_single(
            """
            MATCH (a {node_id: $uid})-[r]-(b {node_id: $vid})
            RETURN type(r) AS rel_type, properties(r) AS props
            LIMIT 1
            """,
            uid=u_id,
            vid=v_id,
        )
        if rec:
            props = rec.get("props", {})
            props["type"] = rec.get("rel_type", "connected")
            return props
        return {}

    def node_count(self) -> int:
        """Return total number of nodes."""
        rec = self._run_single("MATCH (n) RETURN count(n) AS cnt")
        return rec["cnt"] if rec else 0

    def is_connected(self) -> bool:
        """Check if Neo4j is reachable and the database exists."""
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Bulk data retrieval  (for GNN training)
    # ------------------------------------------------------------------
    def get_all_nodes_with_data(self) -> list:
        """Return all nodes as a list of (node_id, properties_dict)."""
        records = self._run("MATCH (n) RETURN n.node_id AS nid, properties(n) AS props")
        return [(r["nid"], r["props"]) for r in records if r.get("nid")]

    def get_all_edges(self) -> list:
        """Return all edges as a list of (u_id, v_id, properties_dict)."""
        records = self._run(
            """
            MATCH (a)-[r]-(b)
            WHERE id(a) < id(b)
            RETURN a.node_id AS uid, b.node_id AS vid,
                   type(r) AS rel_type, properties(r) AS props
            """
        )
        result = []
        for r in records:
            props = r.get("props", {})
            props["type"] = r.get("rel_type", "unknown")
            result.append((r["uid"], r["vid"], props))
        return result

    def get_relationship_type_counts(self, node_id: str) -> dict:
        """Return a frequency map of relationship types touching the given node."""
        records = self._run(
            """
            MATCH (n {node_id: $nid})-[r]-()
            RETURN type(r) AS rel_type, count(r) AS cnt
            """,
            nid=node_id,
        )
        return {
            rec["rel_type"]: int(rec.get("cnt") or 0)
            for rec in records
            if rec.get("rel_type")
        }

    # ------------------------------------------------------------------
    # Statistics & maintenance
    # ------------------------------------------------------------------
    def get_stats(self) -> dict:
        """Return statistics about the graph database."""
        stats = {
            "total_nodes": 0,
            "total_edges": 0,
            "individual_nodes": 0,
            "crime_nodes": 0,
            "protest_nodes": 0,
            "record_nodes": 0,
            "organization_nodes": 0,
            "case_nodes": 0,
            "edge_types": {},
        }

        # Node counts by label
        rec = self._run_single("MATCH (n) RETURN count(n) AS cnt")
        stats["total_nodes"] = rec["cnt"] if rec else 0

        for label, key in [
            ("Individual", "individual_nodes"),
            ("Crime", "crime_nodes"),
            ("Protest", "protest_nodes"),
            ("Record", "record_nodes"),
            ("Organization", "organization_nodes"),
            ("Case", "case_nodes"),
        ]:
            rec = self._run_single(f"MATCH (n:{label}) RETURN count(n) AS cnt")
            stats[key] = rec["cnt"] if rec else 0

        # Edge count (undirected — count each edge once)
        rec = self._run_single(
            "MATCH ()-[r]-() RETURN count(r)/2 AS cnt"
        )
        stats["total_edges"] = rec["cnt"] if rec else 0

        # Edge types
        edge_records = self._run(
            """
            MATCH ()-[r]-()
            RETURN type(r) AS etype, count(r)/2 AS cnt
            """
        )
        for r in edge_records:
            stats["edge_types"][r["etype"]] = r["cnt"]

        return stats

    def clean_junk_nodes(self) -> int:
        """Remove Individual nodes whose names fail the _is_valid_person_name() check.

        Returns the number of nodes removed.
        """
        records = self._run(
            "MATCH (n:Individual) RETURN n.node_id AS nid, n.name AS name"
        )
        to_remove = []
        for r in records:
            name = r.get("name", "")
            if not _is_valid_person_name(name):
                to_remove.append(r["nid"])

        if to_remove:
            # DETACH DELETE removes the node and all its relationships
            self._run(
                """
                UNWIND $nids AS nid
                MATCH (n {node_id: nid})
                DETACH DELETE n
                """,
                nids=to_remove,
            )
            print(
                f"  [Graph Clean] Removed {len(to_remove)} junk Individual node(s)."
            )

        self._log_audit(
            "clean_junk_nodes",
            {"removed_count": len(to_remove), "removed_nodes": to_remove},
        )
        return len(to_remove)


# ---------------------------------------------------------------------------
# PyTorch Graph Neural Network (GCN) Implementation
# ---------------------------------------------------------------------------

if HAS_TORCH:
    class GCNLayer(nn.Module):
        def __init__(self, in_features: int, out_features: int):
            super().__init__()
            self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
            self.bias = nn.Parameter(torch.FloatTensor(out_features))
            nn.init.xavier_uniform_(self.weight)
            nn.init.zeros_(self.bias)

        def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
            support = torch.matmul(x, self.weight)
            if adj_norm.is_sparse:
                output = torch.sparse.mm(adj_norm, support)
            else:
                output = torch.matmul(adj_norm, support)
            return output + self.bias

    class GCN(nn.Module):
        def __init__(self, in_features: int, hidden_dim: int, out_dim: int):
            super().__init__()
            self.gcn1 = GCNLayer(in_features, hidden_dim)
            self.gcn2 = GCNLayer(hidden_dim, out_dim)
            self.activation = nn.ReLU()

        def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
            h = self.gcn1(x, adj_norm)
            h = self.activation(h)
            h = self.gcn2(h, adj_norm)
            return h
else:
    # Fallback placeholder if PyTorch is not available
    class GCN:
        pass


class GNNModelManager:
    def __init__(self, db: GraphDatabase):
        self.db = db
        self.node_embeddings = {}  # maps node_id to np.ndarray
        self.node_id_to_idx = {}
        self.idx_to_node_id = {}
        self.feature_dim = 64
        self.embedding_dim = 32
        self.relation_weight_map = {
            "ACCUSED_IN": 1.35,
            "MEMBER_OF": 1.2,
            "ASSOCIATED_WITH": 1.1,
            "PARTICIPATED_IN": 1.15,
            "CO_OCCURRED_WITH": 1.0,
            "MENTIONED_IN": 0.95,
            "REPORTED_IN": 0.9,
        }

    def _build_feature_matrix(self, texts: list, num_nodes: int):
        """Prefer sentence embeddings, then fall back to TF-IDF."""
        if HAS_TORCH:
            try:
                from app.infrastructure.qdrant.qdrant_service import get_qdrant_service

                qdrant = get_qdrant_service()
                vectors = [qdrant.embed(text or "") for text in texts]
                if vectors and any(any(abs(val) > 1e-9 for val in vec) for vec in vectors):
                    self.feature_dim = len(vectors[0])
                    return torch.FloatTensor(np.asarray(vectors, dtype=np.float32))
            except Exception:
                pass

        vectorizer = TfidfVectorizer(max_features=self.feature_dim, stop_words="english")
        try:
            x_sparse = vectorizer.fit_transform(texts)
            return torch.FloatTensor(x_sparse.toarray())
        except Exception:
            return torch.randn(num_nodes, self.feature_dim)

    def train(self, epochs: int = 100, lr: float = 0.01) -> bool:
        """Extract features from Neo4j, build relation-aware adjacency, and train the GNN."""
        if not HAS_TORCH:
            print("[Warning] PyTorch is not available. Skipping GNN training.")
            return False

        # 1) Pull all nodes from Neo4j
        all_nodes = self.db.get_all_nodes_with_data()
        num_nodes = len(all_nodes)
        if num_nodes < 3:
            print("[Info] Not enough nodes in graph to train GNN.")
            return False

        node_ids = [nid for nid, _ in all_nodes]
        node_data = {nid: props for nid, props in all_nodes}

        # 2) Map node IDs to indices
        self.node_id_to_idx = {nid: idx for idx, nid in enumerate(node_ids)}
        self.idx_to_node_id = {idx: nid for idx, nid in enumerate(node_ids)}

        # 3) Extract node text features using sentence embeddings when available.
        texts = [node_data[nid].get("description", "") for nid in node_ids]
        X = self._build_feature_matrix(texts, num_nodes)

        # 4) Build adjacency matrix with relation-type and temporal weighting.
        all_edges = self.db.get_all_edges()
        import scipy.sparse as sp
        
        # Build sparse matrix A
        row_indices = []
        col_indices = []
        data = []
        
        # Keep track of max weights for (i, j) pairs
        edge_weights = {}
        for u_id, v_id, eprops in all_edges:
            if u_id in self.node_id_to_idx and v_id in self.node_id_to_idx:
                i = self.node_id_to_idx[u_id]
                j = self.node_id_to_idx[v_id]
                if i == j:
                    continue
                rel_weight = self.relation_weight_map.get(eprops.get("type", ""), 1.0)
                temporal_weight = float(eprops.get("weight") or 1.0)
                w = temporal_weight * rel_weight
                pair = (min(i, j), max(i, j))
                edge_weights[pair] = max(edge_weights.get(pair, 0.0), w)

        for (i, j), w in edge_weights.items():
            row_indices.extend([i, j])
            col_indices.extend([j, i])
            data.extend([w, w])

        # Self-loops
        row_indices.extend(range(num_nodes))
        col_indices.extend(range(num_nodes))
        data.extend([1.0] * num_nodes)

        # Create sparse COO matrix
        A_tilde = sp.coo_matrix((data, (row_indices, col_indices)), shape=(num_nodes, num_nodes))
        
        # Degree normalization: D^-1/2 * A_tilde * D^-1/2
        degrees = np.array(A_tilde.sum(axis=1)).flatten()
        deg_inv_sqrt = np.power(degrees, -0.5, where=degrees > 0)
        deg_inv_sqrt[degrees == 0] = 0
        D_inv_sqrt = sp.diags(deg_inv_sqrt)
        
        adj_norm_sparse = D_inv_sqrt.dot(A_tilde).dot(D_inv_sqrt).tocoo()

        # Decide whether to use sparse or dense tensor
        if num_nodes > 1000:
            indices = torch.LongTensor(np.vstack((adj_norm_sparse.row, adj_norm_sparse.col)))
            values = torch.FloatTensor(adj_norm_sparse.data)
            adj_norm = torch.sparse_coo_tensor(indices, values, torch.Size(adj_norm_sparse.shape))
        else:
            adj_norm = torch.FloatTensor(adj_norm_sparse.toarray())

        # 5) Prepare Link Prediction Datasets
        pos_edges = []
        for u_id, v_id, _ in all_edges:
            if u_id in self.node_id_to_idx and v_id in self.node_id_to_idx:
                pos_edges.append((self.node_id_to_idx[u_id], self.node_id_to_idx[v_id]))

        neg_edges = []
        attempts = 0
        neg_set = set()
        while len(neg_edges) < len(pos_edges) and attempts < len(pos_edges) * 10:
            attempts += 1
            u_idx = np.random.randint(0, num_nodes)
            v_idx = np.random.randint(0, num_nodes)
            if u_idx == v_idx:
                continue
            pair = (min(u_idx, v_idx), max(u_idx, v_idx))
            if pair not in edge_weights and (u_idx, v_idx) not in neg_set and (v_idx, u_idx) not in neg_set:
                neg_edges.append((u_idx, v_idx))
                neg_set.add((u_idx, v_idx))

        if not pos_edges:
            print("[Info] No edges in graph to construct GNN training labels.")
            return False

        # 6) Define GNN model, Optimizer, Loss
        model = GCN(in_features=X.shape[1], hidden_dim=48, out_dim=self.embedding_dim)
        optimizer = optim.Adam(model.parameters(), lr=lr)

        def predict_links(embeddings, edge_list):
            u_embeds = embeddings[edge_list[:, 0]]
            v_embeds = embeddings[edge_list[:, 1]]
            scores = torch.sum(u_embeds * v_embeds, dim=1)
            return torch.sigmoid(scores)

        pos_edges_tensor = torch.LongTensor(pos_edges)
        neg_edges_tensor = torch.LongTensor(neg_edges) if neg_edges else torch.empty(0, 2, dtype=torch.long)

        # 7) Train Loop
        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            embeddings = model(X, adj_norm)

            pos_scores = predict_links(embeddings, pos_edges_tensor)
            pos_loss = -torch.log(pos_scores + 1e-6).mean()

            if neg_edges:
                neg_scores = predict_links(embeddings, neg_edges_tensor)
                neg_loss = -torch.log(1.0 - neg_scores + 1e-6).mean()
                loss = pos_loss + neg_loss
            else:
                loss = pos_loss

            loss.backward()
            optimizer.step()

        # 8) Save trained embeddings
        model.eval()
        with torch.no_grad():
            final_embeddings = model(X, adj_norm).numpy()

        self.node_embeddings = {
            self.idx_to_node_id[idx]: final_embeddings[idx]
            for idx in range(num_nodes)
        }

        print(f"[Info] GNN training finished. Generated embeddings for {len(self.node_embeddings)} nodes.")
        return True

    def get_embedding(self, node_id: str) -> np.ndarray:
        """Return the embedding vector for a node. Fallback to random if not trained."""
        if node_id in self.node_embeddings:
            return self.node_embeddings[node_id]
        return np.random.randn(self.embedding_dim)

    def get_similarity(self, node_id_1: str, node_id_2: str) -> float:
        """Calculate cosine similarity between two node embeddings."""
        v1 = self.get_embedding(node_id_1)
        v2 = self.get_embedding(node_id_2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        sim = float(np.dot(v1, v2) / (norm1 * norm2))
        return min(max(sim, -1.0), 1.0)

    def recommend_associates(self, name: str, top_n: int = 3) -> list:
        """Recommend potential hidden associates for an individual based on GNN similarity."""
        node_id = f"ind_{name.lower().replace(' ', '_')}"
        if not self.db.has_node(node_id):
            return []

        # Get all Individual nodes from Neo4j
        all_nodes = self.db.get_all_nodes_with_data()

        scores = []
        for other_id, other_data in all_nodes:
            if other_id == node_id:
                continue
            if other_data.get("type") != "individual":
                continue

            other_name = other_data.get("name", "")
            if not _is_valid_person_name(other_name):
                continue

            sim = self.get_similarity(node_id, other_id)
            # Check direct edge
            edge = self.db.get_edge(node_id, other_id)
            has_direct_edge = bool(edge)
            relationship_hint = edge.get("type") if has_direct_edge else ""
            scores.append((other_name, sim, has_direct_edge, relationship_hint))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]

    def disambiguate_profile(self, name: str, candidate_profiles: list, crime_text: str) -> tuple:
        """Disambiguate an extracted name matching multiple profiles using context scoring,
        LLM coreference checking, and TF-IDF text similarity fallback.

        Returns:
            (best_profile, is_ambiguous)
        """
        if not candidate_profiles:
            return None, False
        if len(candidate_profiles) == 1:
            return candidate_profiles[0], False

        import re
        # 1. Context field scoring
        scored_candidates = []
        for prof in candidate_profiles:
            score = 0
            
            # Parentage match (e.g. S/o Sivadasan)
            parent_matches = re.findall(r"[SsDd]/o\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})", crime_text)
            if prof.parentage and parent_matches:
                for pm in parent_matches:
                    if is_fuzzy_match(pm, prof.parentage):
                        score += 15
                        break
                        
            # Police station match
            if prof.police_station:
                ps_name = prof.police_station.replace(" PS", "").replace(" ps", "").strip()
                if ps_name.lower() in crime_text.lower():
                    score += 10
                    
            # Address word match
            if prof.address:
                addr_words = [w for w in prof.address.replace(",", " ").split() if len(w) > 3]
                for w in addr_words:
                    if w.lower() in crime_text.lower():
                        score += 5
                        break
                        
            scored_candidates.append((prof, score))
            
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Check if there is a clear winner in context scores (e.g. difference of at least 5)
        if len(scored_candidates) > 1 and scored_candidates[0][1] >= scored_candidates[1][1] + 5:
            return scored_candidates[0][0], False
            
        # 2. LLM-assisted coreference resolution
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "qwen:8b")
        
        # Check if Ollama is reachable
        ollama_available = False
        try:
            import requests
            r = requests.get(f"{ollama_url}/api/tags", timeout=2)
            if r.status_code == 200:
                ollama_available = True
                # Resolve preferred model
                tags = [t["name"] for t in r.json().get("models", [])]
                if ollama_model not in tags:
                    for preferred in ["qwen", "qwen2.5", "gemma2", "llama3"]:
                        for t in tags:
                            if t.lower().startswith(preferred):
                                ollama_model = t
                                break
                        if ollama_model in tags:
                            break
        except Exception:
            pass
            
        if ollama_available:
            profiles_context = []
            for idx, prof in enumerate(candidate_profiles):
                profiles_context.append(
                    f"Profile Index: {idx}\n"
                    f"- Name: {prof.name}\n"
                    f"- Parentage: {prof.parentage or 'Unknown'}\n"
                    f"- Residence Address: {prof.address or 'Unknown'}\n"
                    f"- Police Station Jurisdiction: {prof.police_station or 'Unknown'}\n"
                    f"- Activity Type: {prof.activity_type or 'Unknown'}\n"
                )
            
            profiles_str = "\n".join(profiles_context)
            prompt = (
                "You are an expert intelligence analyst for the Kerala Police.\n"
                f"A crime report text mentions the suspect name '{name}'. There are multiple matching suspect profile dossiers in our registry.\n"
                "Review the crime report and the candidate profiles below to determine the most likely suspect matching the report.\n\n"
                f"Crime Report Text:\n\"\"\"{crime_text}\"\"\"\n\n"
                "Candidate Suspect Profiles:\n"
                f"{profiles_str}\n"
                "CRITICAL RULES:\n"
                "1. Evaluate matching details (such as parentage/family, police station, town/address, organization/crime details).\n"
                "2. If one profile is a clear match, return its Profile Index (e.g. 0, 1, 2).\n"
                "3. If there is not enough context or multiple profiles are equally likely, return 'AMBIGUOUS'.\n"
                "4. Return ONLY a valid JSON object of the format: {\"best_match_index\": <index_number_or_null>, \"status\": \"resolved\"/\"ambiguous\"}.\n"
                "No markdown, no explanation, no other text."
            )
            
            try:
                import requests
                resp = requests.post(
                    f"{ollama_url}/api/generate",
                    json={"model": ollama_model, "prompt": prompt, "stream": False, "format": "json"},
                    timeout=20
                )
                if resp.status_code == 200:
                    resp_data = json.loads(resp.json().get("response", "").strip())
                    status = resp_data.get("status")
                    idx_val = resp_data.get("best_match_index")
                    if status == "resolved" and idx_val is not None and 0 <= int(idx_val) < len(candidate_profiles):
                        return candidate_profiles[int(idx_val)], False
                    elif status == "ambiguous":
                        # Explicitly declared ambiguous by LLM, route to fallback or return ambiguous
                        pass
            except Exception as e:
                print(f"[Warning] LLM coreference check failed: {e}. Falling back to TF-IDF.")

        # 3. Fallback to TF-IDF similarity calculation
        profile_texts = []
        for prof in candidate_profiles:
            desc = f"Name: {prof.name}. Parentage: {prof.parentage}. Station: {prof.police_station}. Address: {prof.address}."
            profile_texts.append(desc)

        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(profile_texts + [crime_text])

            cand_vectors = tfidf_matrix[:-1].toarray()
            crime_vector = tfidf_matrix[-1].toarray()[0]

            tf_idf_scores = []
            for idx, vec in enumerate(cand_vectors):
                denom = np.linalg.norm(vec) * np.linalg.norm(crime_vector)
                sim = np.dot(vec, crime_vector) / denom if denom > 0 else 0.0
                tf_idf_scores.append((candidate_profiles[idx], sim))

            tf_idf_scores.sort(key=lambda x: x[1], reverse=True)

            if len(tf_idf_scores) > 1 and tf_idf_scores[0][1] > tf_idf_scores[1][1] + 0.05:
                return tf_idf_scores[0][0], False
            return tf_idf_scores[0][0], True
        except Exception:
            return candidate_profiles[0], True
