import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Profile, Report, ReportItem
from app.modules.graph.graph_service import GraphService
from app.infrastructure.ollama.llm_service import LLMService
from app.infrastructure.qdrant.qdrant_service import QdrantService


class RAGService:
    """Grounded intelligence chat service backed by Qdrant, SQL, Neo4j, and Ollama."""

    def __init__(self):
        self.qdrant = QdrantService()
        self.graph_service = GraphService()
        self.llm_service = LLMService()

    async def chat(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 5,
        graph_depth: int = 1,
    ) -> Dict[str, Any]:
        clean_query = (query or "").strip()
        if not clean_query:
            return {
                "answer": "Please enter an intelligence query.",
                "citations": [],
                "graph_summary": "",
                "used_fallback": True,
                "model": None,
            }

        limit = max(1, min(limit, 8))
        graph_depth = max(1, min(graph_depth, 2))

        citations = await self._collect_citations(db, clean_query, limit)
        graph_summary = await self._collect_graph_summary(db, clean_query, citations, graph_depth)
        answer, model_name, used_fallback = await self._generate_answer(
            clean_query,
            citations,
            graph_summary,
        )

        return {
            "answer": answer,
            "citations": citations,
            "graph_summary": graph_summary,
            "used_fallback": used_fallback,
            "model": model_name,
        }

    async def _collect_citations(
        self,
        db: AsyncSession,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        citations = await self._collect_semantic_citations(db, query, limit)
        if citations:
            return citations[:limit]
        return await self._collect_sql_citations(db, query, limit)

    async def _collect_semantic_citations(
        self,
        db: AsyncSession,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = []
        seen: set[Tuple[str, str]] = set()

        profile_hits = self.qdrant.search(collection="profiles", query=query, limit=limit)
        for hit in profile_hits:
            payload = hit.get("payload") or {}
            profile_id = payload.get("profile_id") or hit.get("id")
            if not profile_id:
                continue
            profile = await db.get(Profile, str(profile_id))
            if not profile:
                continue
            dedup_key = ("profile", profile.id)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            citations.append(
                {
                    "entity_type": "profile",
                    "title": f"{profile.name} (PP/{profile.pp_id or 'PENDING'})",
                    "snippet": (profile.brief_history or profile.address or profile.activity_type or "").strip(),
                    "id": profile.id,
                    "score": float(hit.get("score") or 0.0),
                }
            )

        item_hits = self.qdrant.search(collection="report_items", query=query, limit=limit)
        for hit in item_hits:
            payload = hit.get("payload") or {}
            report_item_id = payload.get("report_item_id") or hit.get("id")
            if not report_item_id:
                continue
            report_item = await db.get(ReportItem, str(report_item_id))
            if not report_item:
                continue
            report = await db.get(Report, report_item.report_id)
            route_id = report.id if report else report_item.report_id
            dedup_key = ("report_item", report_item.id)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            report_label = report.report_date if report else "Unknown Date"
            citations.append(
                {
                    "entity_type": "report_item",
                    "title": f"Report Item ({report_item.category}) - {report_label}",
                    "snippet": (
                        report_item.summary_text
                        or report_item.translated_text
                        or report_item.raw_text
                        or ""
                    ).strip(),
                    "id": route_id,
                    "score": float(hit.get("score") or 0.0),
                }
            )

        citations.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
        return citations[:limit]

    async def _collect_sql_citations(
        self,
        db: AsyncSession,
        query: str,
        limit: int,
    ) -> List[Dict[str, Any]]:
        normalized_query = query.lower().strip()
        citations: List[Dict[str, Any]] = []

        profile_result = await db.execute(
            select(Profile).where(
                or_(
                    Profile.name.ilike(f"%{normalized_query}%"),
                    Profile.address.ilike(f"%{normalized_query}%"),
                    Profile.activity_type.ilike(f"%{normalized_query}%"),
                    Profile.brief_history.ilike(f"%{normalized_query}%"),
                )
            ).limit(limit)
        )
        for profile in profile_result.scalars().all():
            citations.append(
                {
                    "entity_type": "profile",
                    "title": f"{profile.name} (PP/{profile.pp_id or 'PENDING'})",
                    "snippet": (profile.brief_history or profile.address or profile.activity_type or "").strip(),
                    "id": profile.id,
                    "score": None,
                }
            )

        remaining = max(1, limit - len(citations))
        item_result = await db.execute(
            select(ReportItem).where(
                or_(
                    ReportItem.summary_text.ilike(f"%{normalized_query}%"),
                    ReportItem.translated_text.ilike(f"%{normalized_query}%"),
                    ReportItem.raw_text.ilike(f"%{normalized_query}%"),
                )
            ).limit(remaining)
        )
        for item in item_result.scalars().all():
            report = await db.get(Report, item.report_id)
            report_label = report.report_date if report else "Unknown Date"
            citations.append(
                {
                    "entity_type": "report_item",
                    "title": f"Report Item ({item.category}) - {report_label}",
                    "snippet": (item.summary_text or item.translated_text or item.raw_text or "").strip(),
                    "id": item.report_id,
                    "score": None,
                }
            )

        return citations[:limit]

    async def _collect_graph_summary(
        self,
        db: AsyncSession,
        query: str,
        citations: List[Dict[str, Any]],
        graph_depth: int,
    ) -> str:
        if not self.graph_service.db.is_connected():
            return ""

        profile_ids = [item["id"] for item in citations if item.get("entity_type") == "profile"][:2]
        graph_blocks: List[Dict[str, Any]] = []

        for profile_id in profile_ids:
            profile = await db.get(Profile, profile_id)
            if not profile:
                continue
            node_id = profile.neo4j_node_id or f"ind_{profile.name.lower().replace(' ', '_')}"
            graph = self.graph_service.query_subgraph(
                center_node_id=node_id,
                depth=graph_depth,
                query_type="node",
            )
            if graph.get("nodes"):
                graph_blocks.append(graph)

        if not graph_blocks:
            keyword = self._extract_graph_keyword(query)
            if keyword:
                graph = self.graph_service.query_subgraph(
                    query_type="crime",
                    crime_keyword=keyword,
                )
                if graph.get("nodes"):
                    graph_blocks.append(graph)

        if not graph_blocks:
            return ""

        node_labels: Dict[str, List[str]] = {"individual": [], "organization": [], "crime": [], "case": [], "record": []}
        edge_counter: Counter[str] = Counter()
        total_nodes = 0
        total_edges = 0

        for graph in graph_blocks:
            total_nodes += len(graph.get("nodes", []))
            total_edges += len(graph.get("edges", []))
            for node in graph.get("nodes", []):
                node_type = node.get("type") or "unknown"
                label = node.get("label") or node.get("id") or ""
                if node_type in node_labels and label and label not in node_labels[node_type]:
                    node_labels[node_type].append(label)
            for edge in graph.get("edges", []):
                edge_type = edge.get("type")
                if edge_type:
                    edge_counter[edge_type] += 1

        parts = [f"Graph context includes {total_nodes} nodes and {total_edges} relationships."]
        if node_labels["individual"]:
            parts.append("Individuals: " + ", ".join(node_labels["individual"][:5]))
        if node_labels["organization"]:
            parts.append("Organizations: " + ", ".join(node_labels["organization"][:4]))
        if node_labels["crime"]:
            parts.append("Crime nodes: " + ", ".join(node_labels["crime"][:4]))
        if edge_counter:
            rel_summary = ", ".join(
                f"{rel}={count}" for rel, count in edge_counter.most_common(4)
            )
            parts.append("Relationship mix: " + rel_summary)
        return " ".join(parts)

    async def _generate_answer(
        self,
        query: str,
        citations: List[Dict[str, Any]],
        graph_summary: str,
    ) -> Tuple[str, Optional[str], bool]:
        if not citations:
            return (
                "I could not find grounded report, profile, or graph evidence for that query in the current database.",
                None,
                True,
            )

        model_name = await self.llm_service.resolve_model()
        if not model_name:
            return self._build_fallback_answer(citations, graph_summary), None, True

        sources_block = []
        for idx, citation in enumerate(citations, start=1):
            snippet = self._truncate(citation.get("snippet", ""), 260)
            sources_block.append(
                f"[S{idx}] {citation.get('entity_type', 'source').upper()} | "
                f"{citation.get('title', 'Untitled')}\n{snippet}"
            )

        prompt = (
            "You are an intelligence analyst assistant for the Kerala Police.\n"
            "Answer the user's question only from the provided evidence.\n"
            "If evidence is partial, say so clearly.\n"
            "Use short, operational language and cite claims inline as [S1], [S2], etc.\n\n"
            f"Question:\n{query}\n\n"
            f"Graph Context:\n{graph_summary or 'No additional graph context.'}\n\n"
            "Evidence Sources:\n"
            f"{chr(10).join(sources_block)}\n\n"
            "Return only the answer text, with no markdown code fences."
        )

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.llm_service.ollama_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.2},
                    },
                )
            if response.status_code == 200:
                answer = (response.json().get("response") or "").strip()
                if answer:
                    return answer, model_name, False
        except Exception:
            pass

        return self._build_fallback_answer(citations, graph_summary), model_name, True

    def _build_fallback_answer(
        self,
        citations: List[Dict[str, Any]],
        graph_summary: str,
    ) -> str:
        lines = [
            "Here is a grounded summary based on the retrieved intelligence records.",
        ]
        for idx, citation in enumerate(citations[:3], start=1):
            lines.append(
                f"[S{idx}] {citation.get('title')}: {self._truncate(citation.get('snippet', ''), 180)}"
            )
        if graph_summary:
            lines.append("Graph context: " + graph_summary)
        return "\n".join(lines)

    def _extract_graph_keyword(self, query: str) -> str:
        stop_words = {
            "what", "who", "where", "when", "which", "show", "summarize", "summary",
            "active", "about", "from", "into", "with", "their", "have", "this",
            "that", "were", "during", "regarding", "suspect", "reports", "report",
            "intel", "intelligence", "main", "details",
        }
        tokens = re.findall(r"[A-Za-z]{4,}", query.lower())
        for token in tokens:
            if token not in stop_words:
                return token
        return ""

    def _truncate(self, text: str, max_len: int) -> str:
        clean = " ".join((text or "").split())
        if len(clean) <= max_len:
            return clean
        return clean[: max_len - 3].rstrip() + "..."
