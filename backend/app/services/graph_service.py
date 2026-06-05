import app.core.paths  # Configures Python path for importing existing modules
from typing import Dict, List, Any
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

    def query_subgraph(self, center_node_id: str, depth: int = 1) -> Dict[str, Any]:
        """Query Neo4j for nodes and relationships connected to a center node up to a certain depth."""
        if not self.db.is_connected():
            return {"nodes": [], "edges": []}
            
        # If center node ID is not specified or graph is empty, query a general sample of nodes
        if not center_node_id:
            nodes_data = self.db._run("MATCH (n) RETURN n LIMIT 50")
            edges_data = self.db._run("MATCH (a)-[r]-(b) WHERE id(a) < id(b) RETURN a, r, b LIMIT 100")
            
            nodes = []
            seen_nodes = set()
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
                    edges.append({
                        "id": f"e_{aid}_{bid}_{r_rel.type}",
                        "source": aid,
                        "target": bid,
                        "type": r_rel.type,
                        "weight": float(dict(r_rel).get("weight", 1.0))
                    })
            return {"nodes": nodes, "edges": edges}

        # Query sub-graph centered on the node
        # Safe Cypher pattern for depth-based matching
        query = f"""
        MATCH path = (center {{node_id: $center_id}})-[*0..{depth}]-(neighbor)
        RETURN nodes(path) AS path_nodes, relationships(path) AS path_rels
        LIMIT 200
        """
        records = self.db._run(query, center_id=center_node_id)
        
        unique_nodes = {}
        unique_edges = {}
        
        for rec in records:
            path_nodes = rec.get("path_nodes", [])
            path_rels = rec.get("path_rels", [])
            
            for node in path_nodes:
                node_props = dict(node)
                nid = node_props.get("node_id")
                if nid and nid not in unique_nodes:
                    unique_nodes[nid] = self._format_node(node)
            
            for rel in path_rels:
                # Relationship objects returned from neo4j driver contain nodes they connect
                # which can be identified by their internal IDs (rel.nodes[0] and rel.nodes[1])
                # or start/end. Let's lookup nodes by self.db._run to map back to node_id.
                start_element = rel.start_node
                end_element = rel.end_node
                
                # Fetch node_ids for the start and end nodes
                start_props = dict(start_element)
                end_props = dict(end_element)
                
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
                            "weight": float(rel_props.get("weight", 1.0))
                        }
                        
        return {
            "nodes": list(unique_nodes.values()),
            "edges": list(unique_edges.values())
        }

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
