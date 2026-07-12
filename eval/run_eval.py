#!/usr/bin/env python3
"""Run Hearth evaluation against golden Q&A corpus."""
import json
import sys
import time
from pathlib import Path

import httpx
import numpy as np

from metrics import (
    retrieval_hit_rate,
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
    import json as json_module
    answer = ""
    citations = []

    lines = response_text.strip().split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if line.startswith('data: '):
            try:
                data = json_module.loads(line[6:])
                if 'citations' in data:
                    citations = data['citations']
                if 'message' in data and 'content' in data['message']:
                    answer = data['message']['content']
            except json_module.JSONDecodeError:
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
    import asyncio
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

            ready_count = sum(1 for i in items if i.get('status') == 'ready')
            print(f"  Waiting for documents... ({ready_count}/{len(items)} ready)")
            await asyncio.sleep(2)

        raise RuntimeError("Documents did not become ready in time")


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


async def run_eval(url, do_upload):
    if do_upload:
        print("=== Uploading test documents ===")
        await upload_documents(url)
        print("=== Waiting for document processing ===")
        await wait_for_documents_ready(url)

    golden = load_golden()

    results = {
        'retrieval_hit_rates': [],
        'faithfulness_scores': [],
        'answer_relevance_scores': [],
        'latency_ms': [],
    }

    for i, qa in enumerate(golden):
        query = qa['question']
        golden_docs = qa['relevant_documents']
        claims = qa.get('claims', [])

        start = time.time()
        response = await run_query(url, query)
        latency_ms = (time.time() - start) * 1000
        results['latency_ms'].append(latency_ms)

        # Extract document titles from citations
        predicted_docs = [c.get('doc_title', '') for c in response.get('citations', [])]
        citation_texts = [c.get('text', '') for c in response.get('citations', [])]
        answer = response.get('answer', '')

        # Match on document title (case-insensitive substring)
        def doc_match(pred_doc, golden_doc):
            return golden_doc.lower() in pred_doc.lower() or pred_doc.lower() in golden_doc.lower()

        hit_rate = sum(
            1 for g in golden_docs if any(doc_match(p, g) for p in predicted_docs)
        ) / len(golden_docs) if golden_docs else 0.0

        results['retrieval_hit_rates'].append(hit_rate)
        results['faithfulness_scores'].append(
            faithfulness(claims, citation_texts)
        )
        results['answer_relevance_scores'].append(
            answer_relevance_score(query, answer)
        )

        print(f"  Q{i+1}: hit_rate={hit_rate:.2%} "
              f"faithfulness={results['faithfulness_scores'][-1]:.2%} "
              f"relevance={results['answer_relevance_scores'][-1]:.2%} "
              f"latency={latency_ms:.0f}ms")

        # Debug: print citation titles
        if predicted_docs:
            print(f"    Cited docs: {predicted_docs}")

    summary = {
        'retrieval_hit_rate': float(np.mean(results['retrieval_hit_rates'])),
        'faithfulness': float(np.mean(results['faithfulness_scores'])),
        'answer_relevance': float(np.mean(results['answer_relevance_scores'])),
        'latency_p95_ms': float(np.percentile(results['latency_ms'], 95)),
    }

    print(f"\n=== Evaluation Results ===")
    print(f"  Retrieval Hit Rate: {summary['retrieval_hit_rate']:.2%}")
    print(f"  Faithfulness:       {summary['faithfulness']:.2%}")
    print(f"  Answer Relevance:   {summary['answer_relevance']:.2%}")
    print(f"  Latency p95:        {summary['latency_p95_ms']:.0f}ms")

    thresholds = json.loads(THRESHOLDS_FILE.read_text())
    print(f"\n=== Thresholds ===")
    for k, v in thresholds.items():
        print(f"  {k}: {v}")

    passed = all(
        summary.get(k, 0) >= v if not k.endswith('_ms') else summary.get(k, float('inf')) <= v
        for k, v in thresholds.items()
    )

    print(f"\n  {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def main():
    import asyncio
    import argparse
    parser = argparse.ArgumentParser(description='Run Hearth evaluation harness')
    parser.add_argument('--url', default='http://localhost:8765', help='Backend URL')
    parser.add_argument('--upload', action='store_true', help='Upload test documents before eval')
    args = parser.parse_args()

    sys.exit(asyncio.run(run_eval(args.url, args.upload)))


if __name__ == '__main__':
    main()