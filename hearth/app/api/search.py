import logging
import re
import struct
from typing import Any

from fastapi import APIRouter, Query

from app.api.schemas import SearchResponse, SearchResult
from app.providers.registry import provider_registry
from app.storage.database import get_db

router = APIRouter(prefix="/api/search")
logger = logging.getLogger(__name__)


def sanitize_fts_query(query: str) -> str:
    """Clean query string to make it safe for SQLite FTS5 MATCH syntax."""
    # Retain alphanumeric characters, foreign accents, and spaces
    words = re.findall(r"[a-zA-Z0-9\u00C0-\u017F]+", query)
    return " ".join(words)


async def perform_hybrid_search(
    q: str,
    doc_type: str | None = None,
    document_ids: list[str] | None = None,
    limit: int = 50,
) -> list[dict]:
    """Perform hybrid search: 0.7 * cosine similarity + 0.3 * normalized BM25 score."""
    db = await get_db()
    try:
        # 1. Vector Search
        vector_results = {}
        try:
            embedding_provider = provider_registry.get_embedding()
            embeddings = await embedding_provider.embed([q])
            query_vector = embeddings[0] if embeddings else None
            if query_vector:
                packed = struct.pack(f"{len(query_vector)}f", *query_vector)

                # Build vector query
                vec_query = """
                    SELECT c.id, c.document_id, c.content, c.token_count,
                           d.title as doc_title, d.doc_type,
                           chunks_vec.distance
                    FROM chunks_vec
                    JOIN chunks c ON chunks_vec.rowid = c.rowid
                    JOIN documents d ON c.document_id = d.id
                    WHERE chunks_vec.embedding MATCH ?
                      AND k = 50
                """
                params: list[Any] = [packed]
                if doc_type:
                    vec_query += " AND d.doc_type = ?"
                    params.append(doc_type)
                if document_ids:
                    placeholders = ",".join("?" for _ in document_ids)
                    vec_query += f" AND c.document_id IN ({placeholders})"
                    params.extend(document_ids)

                cursor = await db.execute(vec_query, params)
                vec_rows = await cursor.fetchall()
                for row in vec_rows:
                    row_dict = dict(row)
                    chunk_id = row_dict["id"]
                    # Cosine distance to cosine similarity
                    dist = float(row_dict.get("distance", 1.0))
                    similarity = max(0.0, min(1.0, 1.0 - dist))
                    vector_results[chunk_id] = {
                        "chunk_id": chunk_id,
                        "document_id": row_dict["document_id"],
                        "content": row_dict["content"],
                        "doc_title": row_dict["doc_title"],
                        "doc_type": row_dict["doc_type"],
                        "token_count": row_dict["token_count"],
                        "cosine_sim": similarity,
                        "bm25_score": None,
                        "source_type": "document",
                    }
        except Exception as e:
            logger.error("Vector search failed: %s", e)

        # 2. FTS5 Search
        fts_results = {}
        try:
            cleaned_q = sanitize_fts_query(q)
            if cleaned_q:
                # Build FTS5 query
                fts_query_str = """
                    SELECT c.id, c.document_id, c.content, c.token_count,
                           d.title as doc_title, d.doc_type,
                           rank as bm25_score
                    FROM chunks_fts
                    JOIN chunks c ON chunks_fts.rowid = c.rowid
                    JOIN documents d ON c.document_id = d.id
                    WHERE chunks_fts MATCH ?
                """
                fts_params: list[Any] = [cleaned_q]
                if doc_type:
                    fts_query_str += " AND d.doc_type = ?"
                    fts_params.append(doc_type)
                if document_ids:
                    placeholders = ",".join("?" for _ in document_ids)
                    fts_query_str += f" AND c.document_id IN ({placeholders})"
                    fts_params.extend(document_ids)

                fts_query_str += " ORDER BY rank LIMIT 50"

                cursor = await db.execute(fts_query_str, fts_params)
                fts_rows = await cursor.fetchall()
                for row in fts_rows:
                    row_dict = dict(row)
                    chunk_id = row_dict["id"]
                    fts_results[chunk_id] = {
                        "chunk_id": chunk_id,
                        "document_id": row_dict["document_id"],
                        "content": row_dict["content"],
                        "doc_title": row_dict["doc_title"],
                        "doc_type": row_dict["doc_type"],
                        "token_count": row_dict["token_count"],
                        "cosine_sim": 0.0,
                        "bm25_score": float(row_dict.get("bm25_score", 0.0)),
                        "source_type": "document",
                    }
        except Exception as e:
            logger.error("FTS5 search failed: %s", e)

        # 3. Score Normalization & Combination
        # Normalize BM25 scores to [0, 1] range (more negative is better rank)
        if fts_results:
            bm25_scores = [c["bm25_score"] for c in fts_results.values()]
            min_bm25 = min(bm25_scores)
            max_bm25 = max(bm25_scores)
            bm25_range = max_bm25 - min_bm25
            for _chunk_id, c in fts_results.items():
                if bm25_range > 0:
                    c["normalized_bm25"] = (max_bm25 - c["bm25_score"]) / bm25_range
                else:
                    c["normalized_bm25"] = 1.0

        # Merge results
        combined = {}
        for chunk_id, vec_res in vector_results.items():
            combined[chunk_id] = vec_res
            combined[chunk_id]["normalized_bm25"] = 0.0

        for chunk_id, fts_res in fts_results.items():
            if chunk_id in combined:
                combined[chunk_id]["normalized_bm25"] = fts_res.get("normalized_bm25", 0.0)
                combined[chunk_id]["bm25_score"] = fts_res["bm25_score"]
            else:
                combined[chunk_id] = fts_res
                # cosine_sim remains 0.0

        # Calculate hybrid score
        for c in combined.values():
            cos_sim = c.get("cosine_sim", 0.0)
            norm_bm25 = c.get("normalized_bm25", 0.0)
            # score = 0.7 * cosine + 0.3 * BM25
            c["score"] = 0.7 * cos_sim + 0.3 * norm_bm25

        # Sort
        sorted_results = sorted(combined.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results[:limit]
    finally:
        await db.close()


@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1),
    doc_type: str | None = None,
    _folder: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
) -> SearchResponse:
    if not q:
        return SearchResponse(results=[], total=0, page=page, per_page=per_page, query=q)

    offset = (page - 1) * per_page

    # Perform hybrid search for documents
    doc_results = await perform_hybrid_search(
        q=q,
        doc_type=doc_type,
        limit=50
    )

    # Perform FTS5 search for notes (only if doc_type is not specified or doc_type == 'note')
    note_results = []
    if doc_type is None or doc_type == "note":
        db = await get_db()
        try:
            note_cursor = await db.execute(
                """SELECT n.id, n.title, n.content,
                          rank as bm25_score
                   FROM notes_fts
                   JOIN notes n ON notes_fts.rowid = n.rowid
                   WHERE notes_fts MATCH ?
                   ORDER BY rank
                   LIMIT 50""",
                (q,),
            )
            note_rows = await note_cursor.fetchall()

            # Normalize notes BM25 scores
            if note_rows:
                bm25_scores = [float(row["bm25_score"]) for row in note_rows]
                min_bm25 = min(bm25_scores)
                max_bm25 = max(bm25_scores)
                bm25_range = max_bm25 - min_bm25

                for row in note_rows:
                    row_dict = dict(row)
                    content = row_dict["content"] or ""
                    raw_score = float(row_dict.get("bm25_score", 0.0))
                    norm_score = (max_bm25 - raw_score) / bm25_range if bm25_range > 0 else 1.0
                    note_results.append({
                        "chunk_id": row_dict["id"],
                        "document_id": row_dict["id"],
                        "content": content,
                        "doc_title": row_dict["title"],
                        "doc_type": "note",
                        "token_count": len(content.split()),
                        "score": norm_score,
                        "source_type": "note",
                    })
        except Exception as e:
            logger.error("Notes search failed: %s", e)
        finally:
            await db.close()

    # Combine results
    all_results = []
    for r in doc_results:
        all_results.append({
            "chunk_id": r["chunk_id"],
            "document_id": r["document_id"],
            "content": r["content"],
            "doc_title": r["doc_title"],
            "doc_type": r["doc_type"],
            "token_count": r["token_count"],
            "score": r["score"],
            "source_type": r["source_type"],
        })
    for r in note_results:
        all_results.append(r)

    # Sort combined results by score descending
    all_results.sort(key=lambda r: r["score"], reverse=True)

    total = len(all_results)
    paged = all_results[offset : offset + per_page]

    return SearchResponse(
        results=[SearchResult(**r) for r in paged],
        total=total,
        page=page,
        per_page=per_page,
        query=q,
    )
