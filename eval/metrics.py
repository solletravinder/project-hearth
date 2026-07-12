"""Metrics calculations for Hearth evaluation."""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


def retrieval_hit_rate(predicted_chunks, golden_chunks, top_k=10):
    """What % of golden chunks appear in top-K predicted chunks."""
    hits = sum(1 for g in golden_chunks if g in predicted_chunks[:top_k])
    return hits / len(golden_chunks) if golden_chunks else 0.0


def faithfulness(claims, supporting_chunks):
    """What % of claims are supported by retrieved chunks."""
    supported = sum(1 for c in claims if any(supports_claim(c, chunk) for chunk in supporting_chunks))
    return supported / len(claims) if claims else 0.0


def supports_claim(claim, chunk, threshold=0.7):
    """Check if chunk semantically supports the claim."""
    claim_emb = embed_text(claim)
    chunk_emb = embed_text(chunk)
    return cosine_similarity([claim_emb], [chunk_emb])[0][0] >= threshold


def answer_relevance(query, answer, threshold=0.5):
    """Cosine similarity between query and answer embeddings."""
    q_emb = embed_text(query)
    a_emb = embed_text(answer)
    return cosine_similarity([q_emb], [a_emb])[0][0] >= threshold


def answer_relevance_score(query, answer):
    """Return the actual cosine similarity score (not binary)."""
    q_emb = embed_text(query)
    a_emb = embed_text(answer)
    return float(cosine_similarity([q_emb], [a_emb])[0][0])


_embed_model = None


def embedding_model():
    """Load embedding model once (singleton)."""
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embed_model


def embed_text(text):
    """Embed a single text string."""
    model = embedding_model()
    return model.encode([text])[0]