import app.core.paths  # Configures Python path for importing existing modules
from typing import Dict, List, Any, Optional
import numpy as np

from graph_db import GraphDatabase, GNNModelManager
from app.config import settings

class GraphService:
    def __init__(self):
        # Instantiate the existing GraphDatabase wrapper with config settings
        self.db = GraphDatabase(
            uri=settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            database=settings.NEO4J_DATABASE
        )

    def get_stats(self) -> Dict[str, Any]:
        """Fetch general graph database statistics."""
        if not self.db.is_connected():
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "individual_nodes": 0,
                "crime_nodes": 0,
                "record_nodes": 0,
                "organization_nodes": 0,
                "case_nodes": 0,
                "edge_types": {},
            }
        return self.db.get_stats()

    def clean_junk_nodes(self) -> int:
        """Clean invalid individual nodes from the graph."""
        if not self.db.is_connected():
            return 0
        return self.db.clean_junk_nodes()

    def get_associates(self, person_name: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Run GNN training and get recommended associates for a name."""
        if not self.db.is_connected():
            return []
        
        # Instantiate and train GNN manager
        gnn = GNNModelManager(self.db)
        # Train on the current graph data
        gnn.train(epochs=50)
        
        raw_recs = gnn.recommend_associates(person_name, top_n=top_n)
        
        # Map output to frontend GnnRecommendation schema
        recommendations = []
        for name, similarity, has_edge in raw_recs:
            recommendations.append({
                "name": name,
                "similarity": float(similarity),
                "hasEdge": bool(has_edge)
            })
        return recommendations

    def query_subgraph(
        self,
        center_node_id: Optional[str] = None,
        depth: int = 1,
        query_type: str = "node",
        date: Optional[str] = None,
        crime_keyword: Optional[str] = None,
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
        if query_type == "all" or not center_node_id:
            nodes_data = self.db._run("MATCH (n) RETURN n LIMIT 80")
            edges_data = self.db._run(
                "MATCH (a)-[r]-(b) WHERE id(a) < id(b) RETURN a, r, b LIMIT 150"
            )
            return self._build_graph(nodes_data, edges_data)

        # ── Mode: DATE ─────────────────────────────────────────────────────────
        if query_type == "date" and date:
            # Find record nodes with matching date and their connected neighbours
            nodes_data = self.db._run(
                """
                MATCH (rec {type: 'record', date: $date})-[r]-(neighbor)
                RETURN neighbor AS n
                UNION
                MATCH (rec {type: 'record', date: $date})
                RETURN rec AS n
                LIMIT 100
                """,
                date=date,
            )
            edges_data = self.db._run(
                """
                MATCH (rec {type: 'record', date: $date})-[r]-(neighbor)
                RETURN rec AS a, r, neighbor AS b
                LIMIT 200
                """,
                date=date,
            )
            return self._build_graph(nodes_data, edges_data)

        # ── Mode: CRIME keyword ────────────────────────────────────────────────
        if query_type == "crime" and crime_keyword:
            keyword = crime_keyword.lower()
            nodes_data = self.db._run(
                """
                MATCH (c {type: 'crime'})
                WHERE toLower(c.text) CONTAINS $kw OR toLower(c.category) CONTAINS $kw
                MATCH (c)-[r]-(neighbor)
                RETURN neighbor AS n
                UNION
                MATCH (c {type: 'crime'})
                WHERE toLower(c.text) CONTAINS $kw OR toLower(c.category) CONTAINS $kw
                RETURN c AS n
                LIMIT 100
                """,
                kw=keyword,
            )
            edges_data = self.db._run(
                """
                MATCH (c {type: 'crime'})
                WHERE toLower(c.text) CONTAINS $kw OR toLower(c.category) CONTAINS $kw
                MATCH (c)-[r]-(neighbor)
                RETURN c AS a, r, neighbor AS b
                LIMIT 200
                """,
                kw=keyword,
            )
            return self._build_graph(nodes_data, edges_data)

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
                        })
            return {"nodes": nodes, "edges": edges}

        # ── Mode: NODE (person name / generic node_id) ─────────────────────────
        query = f"""
        MATCH path = (center {{node_id: $center_id}})-[*0..{depth}]-(neighbor)
        RETURN nodes(path) AS path_nodes, relationships(path) AS path_rels
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
                start_props = dict(rel.start_node)
                end_props = dict(rel.end_node)
                source_id = start_props.get("node_id")
                target_id = end_props.get("node_id")
                if source_id and target_id:
                    rel_type = rel.type
                    rel_props = dict(rel)
                    edge_id = f"e_{source_id}_{target_id}_{rel_type}"
                    if edge_id not in unique_edges:
                        unique_edges[edge_id] = {
                            "id": edge_id,
                            "source": source_id,
                            "target": target_id,
                            "type": rel_type,
                            "weight": float(rel_props.get("weight", 1.0)),
                        }

        return {
            "nodes": list(unique_nodes.values()),
            "edges": list(unique_edges.values()),
        }

    def _build_graph(
        self,
        nodes_data: List[Any],
        edges_data: List[Any],
    ) -> Dict[str, Any]:
        """Convert raw Neo4j records (with 'n' and 'a/r/b' keys) into node/edge dicts."""
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
            r_rel = record.get("r")
            if not a_node or not b_node or not r_rel:
                continue
            a_props = dict(a_node)
            b_props = dict(b_node)
            aid = a_props.get("node_id")
            bid = b_props.get("node_id")
            if aid and bid:
                edge_id = f"e_{aid}_{bid}_{r_rel.type}"
                if edge_id not in seen_edges:
                    seen_edges.add(edge_id)
                    edges.append({
                        "id": edge_id,
                        "source": aid,
                        "target": bid,
                        "type": r_rel.type,
                        "weight": float(dict(r_rel).get("weight", 1.0)),
                    })
        return {"nodes": nodes, "edges": edges}

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
