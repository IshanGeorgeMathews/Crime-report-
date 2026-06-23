import app.core.paths  # Configures Python path for importing existing modules
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import math
from app.infrastructure.neo4j.graph_db import GraphDatabase, GNNModelManager
from app.config import settings

class GraphService:
    def __init__(self):
        # Instantiate the existing GraphDatabase wrapper with config settings
        self.db = GraphDatabase(
            uri=settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            database=settings.NEO4J_DATABASE
        )
        # Cached GNN model — reused across requests, retrained only on topology change
        self._gnn: Optional[GNNModelManager] = None
        self._gnn_node_count: int = -1  # node count at last training run
        # Pre-warm the sentence-embedding model at service startup so the first
        # real call is instant (QdrantService is already a singleton).
        self._prewarm_qdrant()

    def _prewarm_qdrant(self):
        """Eagerly initialise the QdrantService/SentenceTransformer so the heavy
        model load happens once at startup, not on the first user request."""
        try:
            from app.infrastructure.qdrant.qdrant_service import get_qdrant_service
            get_qdrant_service()._init_qdrant()  # no-op if already done
        except Exception as exc:
            print(f"[GraphService] Qdrant pre-warm skipped: {exc}")

    def _get_gnn(self) -> GNNModelManager:
        """Return the cached GNNModelManager, training/retraining only when the
        graph topology has changed (i.e. the total node count differs from the
        count at the last training run)."""
        current_node_count = 0
        try:
            stats = self.db.get_stats()
            current_node_count = stats.get("total_nodes", 0)
        except Exception:
            pass

        if self._gnn is None or current_node_count != self._gnn_node_count:
            print(f"[GraphService] GNN cache miss (nodes: {self._gnn_node_count} → {current_node_count}). Training…")
            gnn = GNNModelManager(self.db)
            gnn.train(epochs=50)
            self._gnn = gnn
            self._gnn_node_count = current_node_count
        else:
            print("[GraphService] GNN cache hit — skipping training.")

        return self._gnn

    def get_stats(self) -> Dict[str, Any]:
        """Fetch general graph database statistics (returns camelCase keys for frontend)."""
        if not self.db.is_connected():
            return {
                "totalNodes": 0,
                "totalEdges": 0,
                "individualNodes": 0,
                "crimeNodes": 0,
                "recordNodes": 0,
                "organizationNodes": 0,
                "caseNodes": 0,
                "edgeTypes": {},
            }
        raw = self.db.get_stats()
        # Map snake_case keys from GraphDatabase.get_stats() to camelCase for the frontend
        return {
            "totalNodes": raw.get("total_nodes", 0),
            "totalEdges": raw.get("total_edges", 0),
            "individualNodes": raw.get("individual_nodes", 0),
            "crimeNodes": raw.get("crime_nodes", 0),
            "recordNodes": raw.get("record_nodes", 0),
            "organizationNodes": raw.get("organization_nodes", 0),
            "caseNodes": raw.get("case_nodes", 0),
            "edgeTypes": raw.get("edge_types", {}),
        }

    def clean_junk_nodes(self) -> int:
        """Clean invalid individual nodes from the graph."""
        if not self.db.is_connected():
            return 0
        return self.db.clean_junk_nodes()

    def get_associates(self, person_name: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get recommended associates for a name using the cached GNN model.
        The model is only (re)trained when the graph topology has changed.
        """
        if not self.db.is_connected():
            return []

        gnn = self._get_gnn()
        raw_recs = gnn.recommend_associates(person_name, top_n=top_n)

        # Map output to frontend GnnRecommendation schema
        recommendations = []
        for recommendation in raw_recs:
            name, similarity, has_edge = recommendation[:3]
            relationship_hint = recommendation[3] if len(recommendation) > 3 else ""
            recommendations.append({
                "name": name,
                "similarity": float(similarity),
                "hasEdge": bool(has_edge),
                "relationshipHint": relationship_hint,
            })
        return recommendations

    def query_subgraph(
        self,
        center_node_id: Optional[str] = None,
        depth: int = 1,
        query_type: str = "node",
        date: Optional[str] = None,
        crime_keyword: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_weight: float = 0.0,
    ) -> Dict[str, Any]:
        """Query Neo4j graph with multiple strategies:
        - query_type='all'    → return a sample of all nodes
        - query_type='date'   → return all nodes linked to a specific date (date param required)
        - query_type='crime'  → return crime nodes matching keyword + their neighbours
        - query_type='node'   → center on a specific node_id (default behaviour)
        """
        if not self.db.is_connected():
            return {"nodes": [], "edges": []}

        # ── Mode: ALL nodes (sample) ────────────────────────────────────────────
        if query_type == "all" or (not center_node_id and query_type not in ("date", "crime")):
            nodes_data = self.db._run("MATCH (n) RETURN n LIMIT 60")
            edges_data = self.db._run(
                "MATCH (a)-[r]-(b) WHERE elementId(a) < elementId(b) RETURN a, type(r) AS rel_type, properties(r) AS props, b LIMIT 120"
            )
            graph = self._build_graph(nodes_data, edges_data)
            return self._apply_temporal_filters(graph, start_date, end_date, min_weight)

        # ── Mode: DATE ─────────────────────────────────────────────────────────
        if query_type == "date":
            if not date:
                return {"nodes": [], "edges": []}
            # Find record nodes with matching date and their connected neighbours
            nodes_data = self.db._run(
                """
                CALL () {
                    MATCH (rec)-[r]-(neighbor)
                    WHERE rec.type = 'record' AND rec.date = $date
                    RETURN neighbor AS n
                    UNION
                    MATCH (rec)
                    WHERE rec.type = 'record' AND rec.date = $date
                    RETURN rec AS n
                }
                RETURN n LIMIT 150
                """,
                date=date,
            )
            edges_data = self.db._run(
                """
                MATCH (rec)-[r]-(neighbor)
                WHERE rec.type = 'record' AND rec.date = $date
                RETURN rec AS a, type(r) AS rel_type, properties(r) AS props, neighbor AS b
                LIMIT 300
                """,
                date=date,
            )
            graph = self._build_graph(nodes_data, edges_data)
            return self._apply_temporal_filters(graph, start_date or date, end_date or date, min_weight)

        # ── Mode: CRIME keyword ────────────────────────────────────────────────
        if query_type == "crime":
            if not crime_keyword:
                return {"nodes": [], "edges": []}
            keyword = crime_keyword.lower()
            nodes_data = self.db._run(
                """
                CALL () {
                    MATCH (c)
                    WHERE c.type = 'crime' AND (toLower(c.text) CONTAINS $kw OR toLower(c.category) CONTAINS $kw)
                    MATCH (c)-[r]-(neighbor)
                    RETURN neighbor AS n
                    UNION
                    MATCH (c)
                    WHERE c.type = 'crime' AND (toLower(c.text) CONTAINS $kw OR toLower(c.category) CONTAINS $kw)
                    RETURN c AS n
                }
                RETURN n LIMIT 150
                """,
                kw=keyword,
            )
            edges_data = self.db._run(
                """
                MATCH (c)
                WHERE c.type = 'crime' AND (toLower(c.text) CONTAINS $kw OR toLower(c.category) CONTAINS $kw)
                MATCH (c)-[r]-(neighbor)
                RETURN c AS a, type(r) AS rel_type, properties(r) AS props, neighbor AS b
                LIMIT 300
                """,
                kw=keyword,
            )
            graph = self._build_graph(nodes_data, edges_data)
            return self._apply_temporal_filters(graph, start_date, end_date, min_weight)

        # ── Mode: NODE — resolve name → node_id if needed ──────────────────────
        # If the user typed a display name (e.g. "John Smith") rather than a
        # node_id ("ind_john_smith" / "rec_…"), do a case-insensitive name lookup
        # against the graph so the search still finds the node.
        if center_node_id and not any(
            center_node_id.startswith(prefix)
            for prefix in ("ind_", "rec_", "cri_", "org_", "case_")
        ):
            # Attempt exact node_id derivation (individual)
            derived_id = f"ind_{center_node_id.lower().replace(' ', '_')}"
            check = self.db._run(
                "MATCH (n {node_id: $nid}) RETURN n.node_id AS nid LIMIT 1",
                nid=derived_id,
            )
            if check and check[0].get("nid"):
                center_node_id = derived_id
            else:
                # Fuzzy: search by name substring across all nodes
                fuzzy = self.db._run(
                    """
                    MATCH (n)
                    WHERE toLower(n.name) CONTAINS toLower($name)
                    RETURN n.node_id AS nid LIMIT 1
                    """,
                    name=center_node_id,
                )
                if fuzzy and fuzzy[0].get("nid"):
                    center_node_id = fuzzy[0]["nid"]
                else:
                    # Nothing found — return empty
                    return {"nodes": [], "edges": []}

        # ── Mode: specific record node ─────────────────────────────────────────
        if center_node_id.startswith("rec_"):
            nodes_records = self.db._run(
                """
                MATCH (center {node_id: $center_id})-[r]-(neighbor)
                RETURN neighbor AS n
                UNION
                MATCH (center {node_id: $center_id})
                RETURN center AS n
                """,
                center_id=center_node_id,
            )
            rels_records = self.db._run(
                """
                MATCH (center {node_id: $center_id})-[r]-(neighbor)
                WITH center, collect(neighbor) + center AS all_nodes
                UNWIND all_nodes AS n1
                UNWIND all_nodes AS n2
                MATCH (n1)-[rel]->(n2)
                RETURN n1.node_id AS source, n2.node_id AS target,
                       type(rel) AS rel_type, properties(rel) AS props
                """,
                center_id=center_node_id,
            )
            nodes = []
            seen_nodes: set = set()
            for record in nodes_records:
                node = record.get("n")
                if not node:
                    continue
                node_props = dict(node)
                nid = node_props.get("node_id")
                if nid and nid not in seen_nodes:
                    seen_nodes.add(nid)
                    nodes.append(self._format_node(node))
            edges = []
            seen_edges: set = set()
            for record in rels_records:
                src = record.get("source")
                tgt = record.get("target")
                rel_type = record.get("rel_type")
                props = record.get("props") or {}
                if src and tgt and rel_type:
                    edge_id = f"e_{src}_{tgt}_{rel_type}"
                    if edge_id not in seen_edges:
                        seen_edges.add(edge_id)
                        edges.append({
                            "id": edge_id,
                            "source": src,
                            "target": tgt,
                            "type": rel_type,
                            "weight": float(props.get("weight", 1.0)),
                            "rawWeight": float(props.get("base_weight") or props.get("weight", 1.0)),
                            "firstSeen": props.get("first_seen"),
                            "lastSeen": props.get("last_seen"),
                            "occurrenceCount": int(props.get("occurrence_count") or 1),
                            "decayHalfLifeDays": float(props.get("decay_half_life_days") or 60.0),
                        })
            graph = {"nodes": nodes, "edges": edges}
            return self._apply_temporal_filters(graph, start_date, end_date, min_weight, center_node_id=center_node_id)

        # ── Mode: NODE (person name / generic node_id) ─────────────────────────
        query = f"""
        MATCH path = (center {{node_id: $center_id}})-[*0..{depth}]-(neighbor)
        RETURN nodes(path) AS path_nodes,
               [rel in relationships(path) | {{
                   source: startNode(rel).node_id,
                   target: endNode(rel).node_id,
                   type: type(rel),
                   weight: rel.weight,
                   rawWeight: rel.base_weight,
                   firstSeen: rel.first_seen,
                   lastSeen: rel.last_seen,
                   occurrenceCount: rel.occurrence_count,
                   decayHalfLifeDays: rel.decay_half_life_days
               }}] AS path_rels
        LIMIT 200
        """
        records = self.db._run(query, center_id=center_node_id)

        unique_nodes: Dict[str, Any] = {}
        unique_edges: Dict[str, Any] = {}

        for rec in records:
            path_nodes = rec.get("path_nodes", [])
            path_rels = rec.get("path_rels", [])

            for node in path_nodes:
                node_props = dict(node)
                nid = node_props.get("node_id")
                if nid and nid not in unique_nodes:
                    unique_nodes[nid] = self._format_node(node)

            for rel in path_rels:
                source_id = rel.get("source")
                target_id = rel.get("target")
                if source_id and target_id:
                    rel_type = rel.get("type")
                    edge_id = f"e_{source_id}_{target_id}_{rel_type}"
                    if edge_id not in unique_edges:
                        unique_edges[edge_id] = {
                            "id": edge_id,
                            "source": source_id,
                            "target": target_id,
                            "type": rel_type,
                            "weight": float(rel.get("weight") or 1.0),
                            "rawWeight": float(rel.get("rawWeight") or rel.get("weight") or 1.0),
                            "firstSeen": rel.get("firstSeen"),
                            "lastSeen": rel.get("lastSeen"),
                            "occurrenceCount": int(rel.get("occurrenceCount") or 1),
                            "decayHalfLifeDays": float(rel.get("decayHalfLifeDays") or 60.0),
                        }

        graph = {
            "nodes": list(unique_nodes.values()),
            "edges": list(unique_edges.values()),
        }
        return self._apply_temporal_filters(graph, start_date, end_date, min_weight, center_node_id=center_node_id)

    def _build_graph(
        self,
        nodes_data: List[Any],
        edges_data: List[Any],
    ) -> Dict[str, Any]:
        """Convert raw Neo4j records (with 'n' and 'a/rel_type/props/b' keys) into node/edge dicts."""
        nodes = []
        seen_nodes: set = set()
        for record in nodes_data:
            node = record.get("n")
            if not node:
                continue
            node_props = dict(node)
            nid = node_props.get("node_id")
            if nid and nid not in seen_nodes:
                seen_nodes.add(nid)
                nodes.append(self._format_node(node))

        edges = []
        seen_edges: set = set()
        for record in edges_data:
            a_node = record.get("a")
            b_node = record.get("b")
            rel_type = record.get("rel_type")
            props = record.get("props") or {}
            if not a_node or not b_node or not rel_type:
                continue
            a_props = dict(a_node)
            b_props = dict(b_node)
            aid = a_props.get("node_id")
            bid = b_props.get("node_id")
            if aid and bid:
                edge_id = f"e_{aid}_{bid}_{rel_type}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append({
                        "id": edge_id,
                        "source": aid,
                        "target": bid,
                        "type": rel_type,
                        "weight": float(props.get("weight", 1.0)),
                        "rawWeight": float(props.get("base_weight") or props.get("weight", 1.0)),
                        "firstSeen": props.get("first_seen"),
                        "lastSeen": props.get("last_seen"),
                        "occurrenceCount": int(props.get("occurrence_count") or 1),
                        "decayHalfLifeDays": float(props.get("decay_half_life_days") or 60.0),
                    })
        return {"nodes": nodes, "edges": edges}

    def _apply_temporal_filters(
        self,
        graph: Dict[str, Any],
        start_date: Optional[str],
        end_date: Optional[str],
        min_weight: float,
        center_node_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not graph.get("edges"):
            return graph

        start_dt = self._parse_date(start_date)
        end_dt = self._parse_date(end_date)
        reference_dt = end_dt or date.today()
        filters_enabled = bool(start_dt or end_dt or min_weight > 0)
        filtered_edges: List[Dict[str, Any]] = []

        for edge in graph["edges"]:
            first_seen_dt = self._parse_date(edge.get("firstSeen"))
            last_seen_dt = self._parse_date(edge.get("lastSeen"))
            active_weight = self._decayed_weight(edge, reference_dt)
            edge["weight"] = active_weight

            overlaps = True
            if start_dt and last_seen_dt and last_seen_dt < start_dt:
                overlaps = False
            if end_dt and first_seen_dt and first_seen_dt > end_dt:
                overlaps = False
            if min_weight > 0 and active_weight < min_weight:
                overlaps = False

            if not filters_enabled or overlaps:
                filtered_edges.append(edge)

        if not filters_enabled:
            return graph

        keep_node_ids = {edge["source"] for edge in filtered_edges} | {edge["target"] for edge in filtered_edges}
        if center_node_id:
            keep_node_ids.add(center_node_id)

        filtered_nodes = [node for node in graph.get("nodes", []) if node.get("id") in keep_node_ids]
        return {"nodes": filtered_nodes, "edges": filtered_edges}

    def _decayed_weight(self, edge: Dict[str, Any], reference_dt: date) -> float:
        last_seen = self._parse_date(edge.get("lastSeen"))
        base_weight = float(edge.get("weight") or 0.0)
        half_life = max(float(edge.get("decayHalfLifeDays") or 60.0), 1.0)
        if not last_seen:
            return base_weight
        elapsed_days = max((reference_dt - last_seen).days, 0)
        lambda_decay = math.log(2.0) / half_life
        return round(base_weight * math.exp(-lambda_decay * elapsed_days), 4)

    def _parse_date(self, value: Optional[str]):
        if not value:
            return None
        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    def _format_node(self, node: Any) -> Dict[str, Any]:
        """Convert a Neo4j node object into frontend representation."""
        props = dict(node)
        node_id = props.get("node_id", "")
        node_type = props.get("type", "unknown")
        
        # Determine label based on type
        label = props.get("name")
        if not label:
            if node_type == "crime":
                # Summarize text
                text = props.get("text", "")
                label = text[:30] + "..." if len(text) > 30 else text
            elif node_type == "case":
                label = props.get("fir_number")
            elif node_type == "record":
                label = f"Record: {props.get('date')}"
            else:
                label = node_id
                
        # Clean up properties to send in "properties" sub-object
        safe_props = {}
        for k, v in props.items():
            if k not in ["node_id", "type", "description"]:
                safe_props[k] = v
                
        return {
            "id": node_id,
            "label": label,
            "type": node_type,
            "properties": safe_props
        }
