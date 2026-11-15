"""Configuração central: paths, nomes de modelos e parâmetros de chunking.
Tudo que for usado tanto pela ingestão quanto pelo app vive aqui.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Dados ---
MARKDOWN_DIR = "data/markdown"

# --- Qdrant ---
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "licitacao_rag")

# --- Modelos ---
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_MODEL_LITE = os.getenv("GEMINI_MODEL_LITE", "gemini-2.5-flash-lite")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")

# --- Chunking ---
# Cabeçalhos markdown considerados como hierarquia (Título > Capítulo > Seção > Artigo)
MD_HEADERS_TO_SPLIT = [
    ("#", "titulo"),
    ("##", "capitulo"),
    ("###", "secao"),
    ("####", "artigo"),
]
CHUNK_SIZE = 1000          # usado só em blocos que ainda ficarem grandes após split por header
CHUNK_OVERLAP = 150

# --- Recuperação ---
TOP_K_RETRIEVE = int(os.getenv("TOP_K_RETRIEVE", 25))
TOP_K_RERANK = int(os.getenv("TOP_K_RERANK", 5))
