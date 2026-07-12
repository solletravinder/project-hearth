#!/usr/bin/env python3
"""Run Hearth evaluation against golden Q&A corpus.

Tests two independent layers:
  1. Search retrieval quality (works without a real LLM — uses /api/search/)
  2. Full chat pipeline (requires an LLM — uses /api/chat/)
"""
import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

from metrics import (
    faithfulness,
    answer_relevance_score,
)

CORPUS_DIR = Path(__file__).parent / 'test_corpus'
GOLDEN_FILE = CORPUS_DIR / 'golden_qa.json'
THRESHOLDS_FILE = CORPUS_DIR / 'expected_scores.json'
BACKEND_URL = 'http://localhost:8765'
DOCUMENTS_DIR = CORPUS_DIR / 'documents'


def load_golden():
    with open(GOLDEN_FILE) as f:
        return json.load(f)


def parse_sse_response(response_text):
    """Parse SSE response to extract answer and citations from 'done' event."""
    answer = ""
    citations = []

    lines = response_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                if 'citations' in data:
                    citations = data['citations']
                if 'message' in data and 'content' in data['message']:
                    answer = data['message']['content']
            except json.JSONDecodeError:
                continue
    return answer, citations


async def upload_documents(url):
    """Upload all test documents to the backend."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        for doc_file in sorted(DOCUMENTS_DIR.glob('*.txt')):
            with open(doc_file, 'rb') as f:
                content = f.read()

            resp = await client.post(
                f'{url}/api/documents/upload',
                files={'file': (doc_file.name, content, 'text/plain')},
                params={'folder': 'eval'}
            )
            resp.raise_for_status()
            doc = resp.json()
            print(f"  Uploaded: {doc_file.name} (id={doc['id']})")


async def wait_for_documents_ready(url, timeout=120):
    """Poll document status until all eval documents are ready."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        await asyncio.sleep(1)

        start = time.time()
        while time.time() - start < timeout:
            resp = await client.get(f'{url}/api/documents/', params={'folder': 'eval'})
            resp.raise_for_status()
            data = resp.json()
            items = data.get('items', [])

            if not items:
                await asyncio.sleep(1)
                continue

            all_ready = all(item.get('status') == 'ready' for item in items)
            if all_ready:
                print(f"  All {len(items)} documents ready")
                return

            ready_count = sum(1 for item in items if item.get('status') == 'ready')
            print(f"  Waiting for documents... ({ready_count}/{len(items)} ready)")
            await asyncio.sleep(2)

        raise RuntimeError("Documents did not become ready in time")


async def search_documents(url, query):
    """Search via /api/search/ and return result document titles."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f'{url}/api/search/', params={'q': query})
        resp.raise_for_status()
        data = resp.json()
        return data.get('results', [])


async def run_query(url, query):
    """Send query to running Hearth backend and parse SSE response."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f'{url}/api/chat/',
            json={'query': query}
        )
        resp.raise_for_status()
        answer, citations = parse_sse_response(resp.text)
        return {'answer': answer, 'citations': citations}


async def check_model_available(url):
    """Check if a real LLM provider is available (not mock)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check provider availability
            resp = await client.get(f'{url}/api/models/providers')
            resp.raise_for_status()
            data = resp.json()
            providers = data.get('providers', {})
            for name, info in providers.items():
                if info.get('available'):
                    return True
    except Exception:
        pass
    return False


async def run_eval(url, do_upload):
    if do_upload:
        print("=== Uploading test documents ===")
        await upload_documents(url)
        print("=== Waiting for document processing ===")
        await wait_for_documents_ready(url)

    golden = load_golden()
    has_llm = await check_model_available(url)
    print(f"\n  LLM available: {has_llm}")

    # ── Phase 1: Search retrieval quality ────────────────────────────────
    print("\n=== Phase 1: Search Retrieval ===")
    retrieval_results = []
    for i, qa in enumerate(golden):
        query = qa['question']
        golden_docs = qa['relevant_documents']

        start = time.time()
        search_hits = await search_documents(url, query)
        latency_ms = (time.time() - start) * 1000

        # Extract document titles from search results
        predicted_docs = [r.get('doc_title', '') for r in search_hits]
        scores = [r.get('score', 0.0) for r in search_hits]

        def doc_match(pred_doc, golden_doc):
            return (golden_doc.lower() in pred_doc.lower()
                    or pred_doc.lower() in golden_doc.lower())

        hit_rate = (
            sum(1 for g in golden_docs
                if any(doc_match(p, g) for p in predicted_docs))
            / len(golden_docs) if golden_docs else 0.0
        )
        retrieval_results.append(hit_rate)

        top_score = f"{scores[0]:.4f}" if scores else "N/A"
        print(f"  Q{i+1}: hit_rate={hit_rate:.2%} "
              f"top_score={top_score} latency={latency_ms:.0f}ms"
              f" docs={[d for d in predicted_docs[:3]]}")

    avg_retrieval = sum(retrieval_results) / len(retrieval_results)
    print(f"\n  Search Retrieval Hit Rate: {avg_retrieval:.2%}")

    # ── Phase 2: Full chat pipeline (LLM-dependent) ─────────────────────
    chat_latency = []
    chat_faithfulness = []
    chat_relevance = []

    if has_llm:
        print("\n=== Phase 2: Chat Pipeline ===")
        for i, qa in enumerate(golden):
            query = qa['question']
            claims = qa.get('claims', [])

            start = time.time()
            response = await run_query(url, query)
            latency_ms = (time.time() - start) * 1000
            chat_latency.append(latency_ms)

            predicted_docs = [c.get('doc_title', '') for c in response.get('citations', [])]
            citation_texts = [c.get('text', '') for c in response.get('citations', [])]
            answer = response.get('answer', '')

            def doc_match(pred_doc, golden_doc):
                return (golden_doc.lower() in pred_doc.lower()
                        or pred_doc.lower() in golden_doc.lower())

            golden_docs = qa['relevant_documents']
            hit_rate = (
                sum(1 for g in golden_docs
                    if any(doc_match(p, g) for p in predicted_docs))
                / len(golden_docs) if golden_docs else 0.0
            )

            chat_faithfulness.append(faithfulness(claims, citation_texts))
            chat_relevance.append(answer_relevance_score(query, answer))

            print(f"  Q{i+1}: hit_rate={hit_rate:.2%} "
                  f"faithfulness={chat_faithfulness[-1]:.2%} "
                  f"relevance={chat_relevance[-1]:.2%} "
                  f"latency={latency_ms:.0f}ms")
    else:
        print("\n=== Phase 2: Skipped (no LLM loaded) ===")

    # ── Summary ──────────────────────────────────────────────────────────
    summary = {
        'retrieval_hit_rate': avg_retrieval,
    }
    if chat_faithfulness:
        summary['faithfulness'] = sum(chat_faithfulness) / len(chat_faithfulness)
        summary['answer_relevance'] = sum(chat_relevance) / len(chat_relevance)
        summary['latency_p95_ms'] = float(
            sorted(chat_latency)[int(len(chat_latency) * 0.95)]
        )

    print("\n=== Evaluation Results ===")
    print(f"  Retrieval Hit Rate: {summary['retrieval_hit_rate']:.2%}")
    if 'faithfulness' in summary:
        print(f"  Faithfulness:       {summary['faithfulness']:.2%}")
        print(f"  Answer Relevance:   {summary['answer_relevance']:.2%}")
        print(f"  Latency p95:        {summary['latency_p95_ms']:.0f}ms")
    else:
        print("  Faithfulness:       N/A (no LLM)")
        print("  Answer Relevance:   N/A (no LLM)")
        print("  Latency p95:        N/A (no LLM)")

    thresholds = json.loads(THRESHOLDS_FILE.read_text())
    print("\n=== Thresholds ===")
    for k, v in thresholds.items():
        status = ""
        if k in summary:
            val = summary[k]
            if k.endswith('_ms'):
                ok = val <= v
            else:
                ok = val >= v
            status = " ✓" if ok else " ✗"
        print(f"  {k}: {v}{status}")

    # Only enforce thresholds that apply to the current run
    checks = {}
    for k, v in thresholds.items():
        if k not in summary:
            continue
        val = summary[k]
        if k.endswith('_ms'):
            checks[k] = val <= v
        else:
            checks[k] = val >= v

    passed = all(checks.values()) if checks else False
    print(f"\n  {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run Hearth evaluation harness')
    parser.add_argument('--url', default='http://localhost:8765', help='Backend URL')
    parser.add_argument('--upload', action='store_true',
                        help='Upload test documents before eval')
    args = parser.parse_args()

    sys.exit(asyncio.run(run_eval(args.url, args.upload)))


if __name__ == '__main__':
    main()
