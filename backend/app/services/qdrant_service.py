import app.core.paths  # Configures Python path for importing existing modules
import os
from typing import List, Dict, Any, Optional
from app.config import settings

# Qdrant client might not connect if server is down, so we handle it gracefully
class QdrantService:
    def __init__(self):
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.client = None
        self.model = None
        self._initialized = False

    def _init_qdrant(self):
        """Lazy init Qdrant client and SentenceTransformer model."""
        if self._initialized:
            return True
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.exceptions import UnexpectedResponse
            from sentence_transformers import SentenceTransformer
            
            self.client = QdrantClient(host=self.host, port=self.port, timeout=5.0)
            
            # Load sentence transformer model
            print("[Qdrant Service] Loading SentenceTransformer 'all-MiniLM-L6-v2'...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Test connectivity and create collections if they don't exist
            collections = ["report_items", "profiles", "crimes"]
            for col in collections:
                try:
                    self.client.get_collection(col)
                except Exception:
                    # Create collection
                    from qdrant_client.http import models
                    self.client.create_collection(
                        collection_name=col,
                        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                    )
                    print(f"[Qdrant Service] Created collection: {col}")
            self._initialized = True
            return True
        except Exception as e:
            print(f"[Warning] Qdrant/SentenceTransformer initialization failed: {e}. Semantic search disabled.")
            self._initialized = False
            return False

    def embed(self, text: str) -> List[float]:
        """Generate 384-dimension vector embedding."""
        if not self._init_qdrant() or not self.model:
            return [0.0] * 384
        return self.model.encode(text).tolist()

    def upsert_item(self, collection: str, point_id: str, text: str, payload: Dict[str, Any]):
        """Upsert a text entry into Qdrant collection."""
        if not self._init_qdrant() or not self.client:
            return
        try:
            from qdrant_client.http import models
            vector = self.embed(text)
            self.client.upsert(
                collection_name=collection,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
        except Exception as e:
            print(f"[Warning] Failed to upsert to Qdrant collection '{collection}': {e}")

    def delete_item(self, collection: str, point_id: str):
        """Delete a point from Qdrant."""
        if not self._init_qdrant() or not self.client:
            return
        try:
            self.client.delete(
                collection_name=collection,
                points_selector=[point_id]
            )
        except Exception as e:
            print(f"[Warning] Failed to delete from Qdrant collection '{collection}': {e}")

    def search(self, collection: str, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search Qdrant collection for similar vectors with optional payload filters."""
        if not self._init_qdrant() or not self.client:
            return []
        try:
            vector = self.embed(query)
            
            # Build filters if passed
            qdrant_filter = None
            if filters:
                from qdrant_client.http import models
                must_conditions = []
                for k, v in filters.items():
                    if v is not None:
                        must_conditions.append(
                            models.FieldCondition(
                                key=k,
                                match=models.MatchValue(value=v)
                            )
                        )
                if must_conditions:
                    qdrant_filter = models.Filter(must=must_conditions)
                    
            results = self.client.search(
                collection_name=collection,
                query_vector=vector,
                query_filter=qdrant_filter,
                limit=limit
            )
            
            mapped_results = []
            for hit in results:
                mapped_results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                })
            return mapped_results
        except Exception as e:
            print(f"[Warning] Qdrant search failed for collection '{collection}': {e}")
            return []
