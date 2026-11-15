"""Busca na web como fallback quando a base documental interna não cobre a pergunta.
Usado para jurisprudência do TCU, notícias e assuntos fora dos arquivos .md indexados.
"""
from langchain_tavily import TavilySearch
from ingest.config import TAVILY_API_KEY

_busca = None


def _get_busca() -> TavilySearch | None:
    global _busca
    if not TAVILY_API_KEY:
        return None
    if _busca is None:
        _busca = TavilySearch(max_results=5, tavily_api_key=TAVILY_API_KEY)
    return _busca


def buscar_na_web(consulta: str) -> list[dict]:
    """Retorna chunks no MESMO formato dos chunks do Qdrant, pra reaproveitar
    _formatar_trechos e o resto do pipeline sem duplicar lógica.
    Campo extra 'fonte_tipo': 'web', usado pra sinalizar no prompt que é fonte externa.
    """
    busca = _get_busca()
    if busca is None:
        return []
    try:
        resultado = busca.invoke({"query": consulta})
    except Exception as e:
        print(f"[ERRO] Busca web falhou: {e}")
        return []

    chunks = []
    for item in resultado.get("results", []):
        chunks.append({
            "texto": item.get("content", ""),
            "score": item.get("score", 0.0),
            "titulo": item.get("title", "Fonte web"),
            "fonte_url": item.get("url", ""),
            "caminho_hierarquico": "",
            "artigo": "",
            "documento": item.get("url", ""),
            "fonte_tipo": "web",
        })
    return chunks
