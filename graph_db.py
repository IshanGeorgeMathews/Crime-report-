"""
graph_db.py - Graphical Database & GNN Module for Intelligence Relations
========================================================================
Implements:
  - NetworkX graph database for representing relationships between:
      * Records ( consolidated reports )
      * Crimes ( specific event details )
      * Individuals ( suspects / persons of interest )
  - JSON serialization / deserialization of the NetworkX graph.
  - TF-IDF feature extraction for nodes using scikit-learn.
  - Native PyTorch-based Graph Convolutional Network (GCN) for node embeddings.
  - Link prediction training and similarity-based name disambiguation.
"""

import os
import re
import json
from datetime import datetime
import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# ---------------------------------------------------------------------------
# Import Name-validation helper from utils
# ---------------------------------------------------------------------------
from utils import _is_valid_person_name


# ---------------------------------------------------------------------------
# Graph Database Manager
# ---------------------------------------------------------------------------

class GraphDatabase:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.G = nx.Graph()
        self.load()

    def load(self):
        """Load the NetworkX graph from a JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # NetworkX 3.x uses node_link_graph
                self.G = nx.node_link_graph(data)
                print(f"[Info] Loaded graph with {self.G.number_of_nodes()} nodes and {self.G.number_of_edges()} edges.")
            except Exception as e:
                print(f"[Warning] Could not load graph database from {self.filepath}: {e}. Initializing empty graph.")
                self.G = nx.Graph()
        else:
            self.G = nx.Graph()

    def save(self):
        """Save the NetworkX graph to a JSON file."""
        try:
            # node_link_data serializes the graph structures
            data = nx.node_link_data(self.G)
            os.makedirs(os.path.dirname(os.path.abspath(self.filepath)), exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Error] Failed to save graph database: {e}")

    def _log_audit(self, action: str, details: dict):
        """Write a log entry to graph_db_audit.json."""
        audit_path = os.path.join(os.path.dirname(self.filepath), "graph_db_audit.json")
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "details": details
        }
        logs = []
        if os.path.exists(audit_path):
            try:
                with open(audit_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
            except Exception:
                logs = []
        logs.append(log_entry)
        try:
            with open(audit_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Warning] Failed to write to audit log: {e}")

    def add_individual(self, name: str, pp_id: str = "", ps: str = "", address: str = "", activity_type: str = ""):
        """Add or update an Individual node.

        Returns the node_id string on success, or None if *name* fails the
        _is_valid_person_name() validation (prevents junk nodes from entering
        the graph regardless of the call site).
        """
        if not _is_valid_person_name(name):
            return None

        node_id = f"ind_{name.lower().replace(' ', '_')}"
        
        # Check if node already exists and merge attributes
        existing_attrs = self.G.nodes[node_id] if self.G.has_node(node_id) else {}
        
        # Keep non-empty attributes
        merged_attrs = {
            "type": "individual",
            "name": name,
            "pp_id": pp_id or existing_attrs.get("pp_id", ""),
            "police_station": ps or existing_attrs.get("police_station", ""),
            "address": address or existing_attrs.get("address", ""),
            "activity_type": activity_type or existing_attrs.get("activity_type", ""),
            "description": f"Individual name: {name}. PP ID: {pp_id or existing_attrs.get('pp_id', 'None')}. Police Station: {ps or existing_attrs.get('police_station', 'None')}. Address: {address or existing_attrs.get('address', 'None')}. Type of Activity: {activity_type or existing_attrs.get('activity_type', 'None')}."
        }
        self.G.add_node(node_id, **merged_attrs)
        self._log_audit("add_individual", {"node_id": node_id, "name": name, "pp_id": pp_id})
        return node_id

    def clean_junk_nodes(self) -> int:
        """Remove Individual nodes whose names fail the _is_valid_person_name() check.

        This is used to clean up legacy junk nodes created before the name-
        validation guard was in place.  All edges connected to removed nodes
        are also removed by NetworkX automatically.

        Returns the number of nodes removed.
        """
        to_remove = []
        for nid, ndata in list(self.G.nodes(data=True)):
            if ndata.get("type") != "individual":
                continue
            name = ndata.get("name", "")
            if not _is_valid_person_name(name):
                to_remove.append(nid)
        self.G.remove_nodes_from(to_remove)
        if to_remove:
            print(f"  [Graph Clean] Removed {len(to_remove)} junk Individual node(s): "
                  f"{[self.G.nodes[n].get('name', n) if self.G.has_node(n) else n for n in to_remove]}")
        self._log_audit("clean_junk_nodes", {"removed_count": len(to_remove), "removed_nodes": to_remove})
        return len(to_remove)

    def add_record(self, date_str: str, filepath: str = ""):
        """Add or update a Record node."""
        node_id = f"rec_{date_str.replace('.', '_')}"
        self.G.add_node(
            node_id,
            type="record",
            date=date_str,
            filepath=filepath,
            description=f"Intelligence Record consolidated for date {date_str}. File path: {filepath}."
        )
        self._log_audit("add_record", {"node_id": node_id, "date": date_str, "filepath": filepath})
        return node_id

    def add_crime(self, crime_id: str, text: str, district: str = "", category: str = "", date_str: str = ""):
        """Add or update a Crime/Event node."""
        node_id = f"cri_{crime_id}"
        self.G.add_node(
            node_id,
            type="crime",
            text=text,
            district=district,
            category=category,
            date=date_str,
            description=f"Crime Event: {text[:200]}... District: {district}. Category: {category}. Date: {date_str}."
        )
        self._log_audit("add_crime", {"node_id": node_id, "district": district, "date": date_str})
        return node_id

    def add_relation(self, u_id: str, v_id: str, rel_type: str, weight: float = 1.0):
        """Add or update an edge between u_id and v_id with structural type constraints."""
        if not self.G.has_node(u_id) or not self.G.has_node(v_id):
            return
        
        type_u = self.G.nodes[u_id].get("type")
        type_v = self.G.nodes[v_id].get("type")
        
        # Enforce structural type constraints
        valid_rels = {
            ("individual", "crime"): {"ASSOCIATED_WITH"},
            ("crime", "individual"): {"ASSOCIATED_WITH"},
            
            ("individual", "record"): {"MENTIONED_IN"},
            ("record", "individual"): {"MENTIONED_IN"},
            
            ("individual", "individual"): {"CO_OCCURRED_WITH"},
            
            ("crime", "record"): {"REPORTED_IN"},
            ("record", "crime"): {"REPORTED_IN"},
        }
        
        pair = (type_u, type_v)
        if pair not in valid_rels or rel_type not in valid_rels[pair]:
            print(f"[Warning] Rejecting invalid relation: {u_id} ({type_u}) -[{rel_type}]-> {v_id} ({type_v})")
            return

        if self.G.has_edge(u_id, v_id):
            # Increase weight for co-occurrence or merge relations
            existing_weight = self.G[u_id][v_id].get("weight", 1.0)
            self.G[u_id][v_id]["weight"] = existing_weight + weight
            self._log_audit("update_relation", {"u_id": u_id, "v_id": v_id, "rel_type": rel_type, "weight": existing_weight + weight})
        else:
            self.G.add_edge(u_id, v_id, type=rel_type, weight=weight)
            self._log_audit("add_relation", {"u_id": u_id, "v_id": v_id, "rel_type": rel_type, "weight": weight})

    def get_stats(self) -> dict:
        """Return statistics about the graph database."""
        stats = {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "individual_nodes": 0,
            "crime_nodes": 0,
            "record_nodes": 0,
            "edge_types": {}
        }
        for _, ndata in self.G.nodes(data=True):
            ntype = ndata.get("type", "unknown")
            if ntype == "individual":
                stats["individual_nodes"] += 1
            elif ntype == "crime":
                stats["crime_nodes"] += 1
            elif ntype == "record":
                stats["record_nodes"] += 1
                
        for _, _, edata in self.G.edges(data=True):
            etype = edata.get("type", "unknown")
            stats["edge_types"][etype] = stats["edge_types"].get(etype, 0) + 1
            
        return stats


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

    def train(self, epochs: int = 100, lr: float = 0.01) -> bool:
        """Extract features, build normalized adjacency, and train PyTorch GCN for link prediction."""
        if not HAS_TORCH:
            print("[Warning] PyTorch is not available. Skipping GNN training.")
            return False

        G = self.db.G
        nodes = list(G.nodes())
        num_nodes = len(nodes)
        if num_nodes < 3:
            print("[Info] Not enough nodes in graph to train GNN.")
            return False

        # 1) Map node IDs to indices
        self.node_id_to_idx = {nid: idx for idx, nid in enumerate(nodes)}
        self.idx_to_node_id = {idx: nid for idx, nid in enumerate(nodes)}

        # 2) Extract Node Text Features using TF-IDF
        texts = []
        for nid in nodes:
            texts.append(G.nodes[nid].get("description", ""))
            
        vectorizer = TfidfVectorizer(max_features=self.feature_dim, stop_words="english")
        try:
            X_sparse = vectorizer.fit_transform(texts)
            X = torch.FloatTensor(X_sparse.toarray())
        except Exception:
            # Fallback to random features if TF-IDF fails (e.g. empty descriptions)
            X = torch.randn(num_nodes, self.feature_dim)

        # 3) Build Adjacency Matrix
        A = nx.to_numpy_array(G, nodelist=nodes, weight="weight")
        # Self-loops
        A_tilde = A + np.eye(num_nodes)
        # Degree normalization
        degrees = np.sum(A_tilde, axis=1)
        deg_inv_sqrt = np.power(degrees, -0.5, where=degrees > 0)
        deg_inv_sqrt[degrees == 0] = 0
        D_inv_sqrt = np.diag(deg_inv_sqrt)
        adj_norm_np = D_inv_sqrt @ A_tilde @ D_inv_sqrt
        
        adj_norm = torch.FloatTensor(adj_norm_np)

        # 4) Prepare Link Prediction Datasets
        # Positive samples (existing edges)
        pos_edges = []
        for u, v in G.edges():
            pos_edges.append((self.node_id_to_idx[u], self.node_id_to_idx[v]))
            
        # Negative samples (non-existing edges)
        neg_edges = []
        # Sample roughly equal number of negative edges
        attempts = 0
        while len(neg_edges) < len(pos_edges) and attempts < len(pos_edges) * 10:
            attempts += 1
            u_idx = np.random.randint(0, num_nodes)
            v_idx = np.random.randint(0, num_nodes)
            if u_idx == v_idx:
                continue
            u_node = self.idx_to_node_id[u_idx]
            v_node = self.idx_to_node_id[v_idx]
            if not G.has_edge(u_node, v_node) and (u_idx, v_idx) not in neg_edges and (v_idx, u_idx) not in neg_edges:
                neg_edges.append((u_idx, v_idx))

        if not pos_edges:
            print("[Info] No edges in graph to construct GNN training labels.")
            return False

        # 5) Define GNN model, Optimizer, Loss
        model = GCN(in_features=X.shape[1], hidden_dim=48, out_dim=self.embedding_dim)
        optimizer = optim.Adam(model.parameters(), lr=lr)
        
        # Link prediction classification function: Sigmoid of dot-product
        def predict_links(embeddings, edge_list):
            u_embeds = embeddings[edge_list[:, 0]]
            v_embeds = embeddings[edge_list[:, 1]]
            # Dot product along the embedding dimension
            scores = torch.sum(u_embeds * v_embeds, dim=1)
            return torch.sigmoid(scores)

        pos_edges_tensor = torch.LongTensor(pos_edges)
        neg_edges_tensor = torch.LongTensor(neg_edges) if neg_edges else torch.empty(0, 2, dtype=torch.long)

        # 6) Train Loop
        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            embeddings = model(X, adj_norm)
            
            # Positive loss
            pos_scores = predict_links(embeddings, pos_edges_tensor)
            pos_loss = -torch.log(pos_scores + 1e-6).mean()
            
            # Negative loss
            if neg_edges:
                neg_scores = predict_links(embeddings, neg_edges_tensor)
                neg_loss = -torch.log(1.0 - neg_scores + 1e-6).mean()
                loss = pos_loss + neg_loss
            else:
                loss = pos_loss
                
            loss.backward()
            optimizer.step()

        # 7) Save trained embeddings
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
        """Recommend potential hidden associates for an individual based on GNN embedding similarity.

        Only returns candidates that pass the _is_valid_person_name() check so
        that historical junk nodes (place names, org names, etc.) are never
        surfaced as recommendations even if they still exist in the graph.
        """
        node_id = f"ind_{name.lower().replace(' ', '_')}"
        if not self.db.G.has_node(node_id):
            return []

        scores = []
        for other_id, other_data in self.db.G.nodes(data=True):
            if other_id == node_id:
                continue
            if other_data.get("type") != "individual":
                continue

            other_name = other_data.get("name", "")
            # Skip any individual node whose name fails the person-name check
            if not _is_valid_person_name(other_name):
                continue

            # Calculate similarity
            sim = self.get_similarity(node_id, other_id)
            # Check if they already have an edge in the graph
            has_direct_edge = self.db.G.has_edge(node_id, other_id)

            scores.append((other_name, sim, has_direct_edge))

        # Sort by similarity descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]

    def disambiguate_profile(self, name: str, candidate_profiles: list, crime_text: str) -> tuple:
        """Disambiguate an extracted name matching multiple profiles using GNN text similarity.
        
        Returns:
            (best_profile, is_ambiguous)
        """
        if not candidate_profiles:
            return None, False
        if len(candidate_profiles) == 1:
            return candidate_profiles[0], False

        # Fit a mini TF-IDF model on the candidate profiles and the crime_text to see which profile aligns closest.
        # This acts as a localized text embedding scorer.
        profile_texts = []
        for prof in candidate_profiles:
            desc = f"Name: {prof.name}. Parentage: {prof.parentage}. Station: {prof.police_station}. Address: {prof.address}."
            profile_texts.append(desc)
            
        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(profile_texts + [crime_text])
            
            # Compute cosine similarity between the candidates (rows 0 to N-1) and the crime_text (row N)
            cand_vectors = tfidf_matrix[:-1].toarray()
            crime_vector = tfidf_matrix[-1].toarray()[0]
            
            scores = []
            for idx, vec in enumerate(cand_vectors):
                denom = np.linalg.norm(vec) * np.linalg.norm(crime_vector)
                sim = np.dot(vec, crime_vector) / denom if denom > 0 else 0.0
                scores.append((candidate_profiles[idx], sim))
                
            scores.sort(key=lambda x: x[1], reverse=True)
            
            # Check if top score is clearly better
            if len(scores) > 1 and scores[0][1] > scores[1][1] + 0.05:
                return scores[0][0], False
            return scores[0][0], True
        except Exception:
            # Fallback to default first element
            return candidate_profiles[0], True
