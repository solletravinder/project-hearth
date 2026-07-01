"""Hybrid search: FTS5 + vector (vector stub for Phase 2)."""

from fastapi import APIRouter, Query

from app.storage.database import get_db

router = APIRouter(prefix="/api/search")


@router.get("/")
async def search(
    q: str = Query(..., min_length=1),
    doc_type: str | None = None,  # noqa: ARG001 — reserved for future filtering
    folder: str | None = None,  # noqa: ARG001 — reserved for future filtering
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
):
    if not q:
        return {"results": [], "total": 0, "page": page, "per_page": per_page}

    offset = (page - 1) * per_page
    db = await get_db()
    try:
        # FTS5 search with BM25 ranking
        # Using external content FTS5 table linked to chunks
        fts_query = q
        cursor = await db.execute(
            """SELECT c.id, c.document_id, c.chunk_index, c.content, c.token_count,
                      d.title as doc_title, d.doc_type, d.status,
                      rank as bm25_score
               FROM chunks_fts
               JOIN chunks c ON chunks_fts.rowid = c.rowid
               JOIN documents d ON c.document_id = d.id
               WHERE chunks_fts MATCH ?
               ORDER BY rank
               LIMIT ? OFFSET ?""",
            (fts_query, per_page, offset),
        )
        rows = await cursor.fetchall()

        # Count total
        count_cursor = await db.execute(
            "SELECT COUNT(*) FROM chunks_fts WHERE chunks_fts MATCH ?",
            (fts_query,),
        )
        total_row = await count_cursor.fetchone()
        total = total_row[0] if total_row else 0

        results = []
        for row in rows:
            row_dict = dict(row)
            results.append(
                {
                    "chunk_id": row_dict["id"],
                    "document_id": row_dict["document_id"],
                    "content": row_dict["content"],
                    "doc_title": row_dict["doc_title"],
                    "doc_type": row_dict["doc_type"],
                    "token_count": row_dict["token_count"],
                    "score": 1.0 - float(row_dict.get("bm25_score", 0)),
                }
            )

        return {
            "results": results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "query": q,
        }
    finally:
        await db.close()
