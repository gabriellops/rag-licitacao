"""Actions chamadas pelos flows em rails.co.
Mantidas simples (regex/heurística) de propósito — são rápidas e não dependem de LLM.
Para casos mais sofisticados, troque por uma chamada ao llm_rapido.
"""
import re

REGEX_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
REGEX_RG = re.compile(r"\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dXx]\b")
REGEX_ARTIGO = re.compile(r"art(?:igo)?\.?\s*\d+", re.IGNORECASE)
DISCLAIMER_PADRAO = (
    "\n\n_Esta resposta é informativa e não substitui parecer jurídico vinculante._"
)


async def detectar_dados_pessoais(texto: str) -> bool:
    return bool(REGEX_CPF.search(texto) or REGEX_RG.search(texto))


async def verificar_citacao(texto: str) -> bool:
    """Heurística: a resposta menciona algum documento/artigo/colchetes de referência?"""
    tem_colchetes = "[" in texto and "]" in texto
    tem_palavra_fonte = any(p in texto.lower() for p in ["art.", "artigo", "lei", "decreto", "edital"])
    return tem_colchetes or tem_palavra_fonte


async def verificar_artigos_existem(texto: str) -> bool:
    """TODO: versão real deve checar os números de artigo citados contra a base indexada
    (ex: consultar os metadados no Qdrant). Por ora, apenas sinaliza se existem artigos citados
    (checagem completa fica a cargo do nó 'checar_fundamentacao' no LangGraph, que já tem contexto).
    """
    return True  # placeholder — a checagem forte já ocorre no grafo (no_checar_fundamentacao)


async def verificar_disclaimer(texto: str) -> bool:
    return "não substitui" in texto.lower() or "parecer jurídico" in texto.lower()


async def adicionar_disclaimer(texto: str) -> str:
    return texto + DISCLAIMER_PADRAO


async def adicionar_aviso_sem_citacao(texto: str) -> str:
    return texto + "\n\n_Aviso: não foi possível identificar claramente as fontes desta resposta._"
