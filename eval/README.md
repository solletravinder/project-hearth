# Hearth Evaluation Harness

Evaluates Hearth's RAG pipeline against a golden Q&A corpus.

## Prerequisites

```bash
pip install sentence-transformers scikit-learn httpx numpy
```

## Running Evaluation

1. Start Hearth backend:
```bash
cd hearth
uv run uvicorn app.main:app --port 8765
```

2. In another terminal, run eval:
```bash
cd eval
python run_eval.py
```

## Files

- `metrics.py` - Metric calculations (hit rate, faithfulness, relevance)
- `run_eval.py` - Main evaluation runner
- `test_corpus/golden_qa.json` - Golden Q&A pairs with expected chunks/claims
- `test_corpus/expected_scores.json` - CI threshold requirements
- `test_corpus/documents/` - Sample documents for ingestion

## Metrics

| Metric | Description |
|--------|-------------|
| Retrieval Hit Rate | % of golden chunks in top-K retrieved |
| Faithfulness | % of claims supported by retrieved chunks |
| Answer Relevance | Cosine similarity(query, answer) |
| Latency p95 | 95th percentile response time (ms) |

## CI Integration

Add to `.github/workflows/ci.yml`:
```yaml
eval:
  runs-on: ubuntu-latest
  needs: test
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.11" }
    - name: Install deps
      run: |
        pip install sentence-transformers scikit-learn httpx numpy
    - name: Start backend
      run: |
        cd hearth && uv run uvicorn app.main:app &
        sleep 15
    - name: Run eval
      run: cd eval && python run_eval.py
```