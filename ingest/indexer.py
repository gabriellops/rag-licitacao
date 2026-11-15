"""Gera embeddings (bge-m3) e sobe os chunks para o Qdrant Cloud.
Rodar uma vez (ou sempre que a base markdown mudar):
    python -m ingest.indexer
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_huggingface import HuggingFaceEmbeddings

from ingest.config import (
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, EMBEDDING_MODEL,
)
from ingest.chunking import processar_toda_base


def get_embedder() -> HuggingFaceEmbeddings:
    # bge-m3 funciona bem em português e permite embeddings densos (usados aqui).
    # TODO: se quiser busca híbrida de verdade, trocar por FlagEmbedding (BGEM3FlagModel)
    # para gerar vetores esparsos também e configurar a collection do Qdrant com named vectors.
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def garantir_colecao(client: QdrantClient, dim: int):
    colecoes = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in colecoes:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print(f"Coleção '{QDRANT_COLLECTION}' criada (dim={dim}).")
    else:
        print(f"Coleção '{QDRANT_COLLECTION}' já existe.")


def indexar():
    print("Carregando e chunkando markdowns...")
    chunks = processar_toda_base()
    print(f"{len(chunks)} chunks gerados.")

    print(f"Carregando modelo de embedding: {EMBEDDING_MODEL} (pode demorar na primeira vez)")
    embedder = get_embedder()

    textos = [c.page_content for c in chunks]
    vetores = embedder.embed_documents(textos)
    dim = len(vetores[0])

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    garantir_colecao(client, dim)

    pontos = [
        PointStruct(
            id=i,
            vector=vetores[i],
            payload={**chunks[i].metadata, "texto": chunks[i].page_content},
        )
        for i in range(len(chunks))
    ]

    # Upload em lotes para não estourar payload da API
    tamanho_lote = 100
    for inicio in range(0, len(pontos), tamanho_lote):
        lote = pontos[inicio:inicio + tamanho_lote]
        client.upsert(collection_name=QDRANT_COLLECTION, points=lote)
        print(f"Upload: {inicio + len(lote)}/{len(pontos)}")

    print("Indexação concluída.")


if __name__ == "__main__":
    indexar()
