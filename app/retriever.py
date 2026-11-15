"""Recuperação de chunks no Qdrant.
Hoje: busca densa (cosine) com bge-m3.
TODO: ativar busca híbrida (denso + esparso/BM25) nativa do Qdrant quando migrar
a indexação para named vectors (ver TODO em ingest/indexer.py).
"""
from qdrant_client import QdrantClient
from langchain_huggingface import HuggingFaceEmbeddings

from ingest.config import (
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_MODEL, TOP_K_RETRIEVE,
)

_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
_embedder = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def recuperar_chunks(pergunta: str, top_k: int = TOP_K_RETRIEVE, filtro: dict | None = None) -> list[dict]:
    """Retorna lista de dicts: {texto, score, documento, tipo, caminho_hierarquico, artigo}.
    `filtro` pode restringir por metadado, ex: {"tipo": "lei"}.
    """
    vetor_pergunta = _embedder.embed_query(pergunta)

    query_filter = None
    if filtro:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        query_filter = Filter(
            must=[FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filtro.items()]
        )

    resposta = _client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=vetor_pergunta,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    )

    chunks = []
    for r in resposta.points:
        payload = r.payload or {}
        chunks.append({
            "texto": payload.get("texto", ""),
            "score": r.score,
            "documento": payload.get("documento", ""),
            "titulo": payload.get("titulo", payload.get("documento", "")),
            "tipo": payload.get("tipo", ""),
            "fonte_url": payload.get("fonte_url", ""),
            "caminho_hierarquico": payload.get("caminho_hierarquico", ""),
            "artigo": payload.get("artigo", ""),
        })
    return chunks
