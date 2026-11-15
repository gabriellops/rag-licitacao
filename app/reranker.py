"""Reordena os chunks recuperados com BAAI/bge-reranker-v2-m3.
Reduz de TOP_K_RETRIEVE (ex: 25) para TOP_K_RERANK (ex: 5) chunks mais relevantes.
"""
from FlagEmbedding import FlagReranker

from ingest.config import RERANKER_MODEL, TOP_K_RERANK

_reranker = None


def _get_reranker() -> FlagReranker:
    global _reranker
    if _reranker is None:
        # use_fp16=True acelera bastante em GPU; em CPU (ex: HF Spaces free) deixe False se der erro
        _reranker = FlagReranker(RERANKER_MODEL, use_fp16=True)
    return _reranker


def rerank_chunks(pergunta: str, chunks: list[dict], top_k: int = TOP_K_RERANK) -> list[dict]:
    if not chunks:
        return []

    reranker = _get_reranker()
    pares = [[pergunta, c["texto"]] for c in chunks]
    scores = reranker.compute_score(pares, normalize=True)

    # compute_score pode devolver float único se só houver 1 par
    if isinstance(scores, float):
        scores = [scores]

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = score

    chunks_ordenados = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
    return chunks_ordenados[:top_k]
