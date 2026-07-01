"""Pipeline orchestrator -- entry point for starting ingestion."""

import logging

from app.pipeline.ingest_workflow import IngestionState, build_ingestion_graph
from app.storage.repository import update_document_status

logger = logging.getLogger(__name__)

_ingestion_graph = None


def get_ingestion_graph():
    global _ingestion_graph
    if _ingestion_graph is None:
        _ingestion_graph = build_ingestion_graph()
    return _ingestion_graph


async def run_ingestion(document_id: str, file_path: str, doc_type: str, title: str) -> dict:
    """Run the ingestion pipeline for a document."""
    try:
        initial_state: IngestionState = {
            "document_id": document_id,
            "document_title": title,
            "file_path": file_path,
            "doc_type": doc_type,
            "raw_text": None,
            "chunks": [],
            "error": None,
            "status": "processing",
        }
        await update_document_status(document_id, "processing")
        graph = get_ingestion_graph()
        result = await graph.ainvoke(initial_state)
        logger.info(f"Ingestion complete for {document_id}: status={result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Ingestion failed for {document_id}: {e}")
        await update_document_status(document_id, "error")
        return {"status": "error", "error": str(e)}
