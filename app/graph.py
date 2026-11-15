"""Fluxo LangGraph:

pergunta
  -> classificar (em escopo?)
  -> reescrever consulta
  -> recuperar (Qdrant) -> rerank
  -> avaliar relevância --(insuficiente, até 2 loops)--> reescrever
  -> gerar resposta com citações
  -> checar fundamentação
  -> resposta + fontes

Os guardrails de entrada/saída (NeMo) envolvem a chamada a este grafo em app/main.py
ou em ui/streamlit_app.py — não ficam dentro do grafo para manter as responsabilidades separadas.
"""

import time

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.llm import llm_principal, llm_rapido
from app.retriever import recuperar_chunks
from app.reranker import rerank_chunks
from app.prompts import (
    PROMPT_CLASSIFICAR, PROMPT_REESCREVER, PROMPT_AVALIAR_RELEVANCIA,
    PROMPT_GERAR_RESPOSTA, PROMPT_CHECAR_FUNDAMENTACAO,
)

MAX_LOOPS_REESCRITA = 2

def cronometrar(nome_etapa):
    """Decorator que imprime quanto tempo cada nó do grafo levou."""
    def decorador(funcao):
        def wrapper(estado):
            inicio = time.time()
            resultado = funcao(estado)
            duracao = time.time() - inicio
            print(f"[TEMPO] {nome_etapa}: {duracao:.2f}s")
            return resultado
        return wrapper
    return decorador

class EstadoRAG(TypedDict, total=False):
    pergunta_original: str
    consulta_atual: str
    historico: str
    em_escopo: bool
    chunks: list[dict]
    tentativas: int
    relevante: bool
    resposta: str
    fontes: list[dict]

@cronometrar("classificar")
def no_classificar(estado: EstadoRAG) -> EstadoRAG:
    resp = llm_rapido.invoke(PROMPT_CLASSIFICAR.format(pergunta=estado["pergunta_original"]))
    estado["em_escopo"] = "licitacao" in resp.content.lower()
    return estado

@cronometrar("reescrever")
def no_reescrever(estado: EstadoRAG) -> EstadoRAG:
    base = estado.get("consulta_atual") or estado["pergunta_original"]
    resp = llm_rapido.invoke(PROMPT_REESCREVER.format(
        pergunta=base, historico=estado.get("historico", "")
    ))
    estado["consulta_atual"] = resp.content.strip()
    estado["tentativas"] = estado.get("tentativas", 0) + 1
    return estado


@cronometrar("recuperar")
def no_recuperar(estado: EstadoRAG) -> EstadoRAG:
    # Reranker desativado: usa direto o top da busca densa do Qdrant.
    # Reduz drasticamente o tempo de resposta; reavaliar se a qualidade cair.
    brutos = recuperar_chunks(estado["consulta_atual"])
    estado["chunks"] = brutos[: 8]  # equivalente ao TOP_K_RERANK, mas sem reordenar
    return estado


def _chave_fonte(c: dict) -> tuple:
    return (c["titulo"], c["caminho_hierarquico"] or c["artigo"])


def _numerar_fontes(chunks: list[dict]) -> dict:
    """Um número por fonte única (ordem de aparição), para que as citações
    [n] no texto batam com a lista de fontes exibida."""
    numeros = {}
    for c in chunks:
        numeros.setdefault(_chave_fonte(c), len(numeros) + 1)
    return numeros


def _formatar_trechos(chunks: list[dict]) -> str:
    numeros = _numerar_fontes(chunks)
    linhas = []
    for c in chunks:
        ref_legivel = c["caminho_hierarquico"] or c["artigo"] or c["documento"]
        linhas.append(f"[{numeros[_chave_fonte(c)]}] {ref_legivel}\n{c['texto']}")
    return "\n\n---\n\n".join(linhas)

@cronometrar("avaliar_relevancia")
def no_avaliar_relevancia(estado: EstadoRAG) -> EstadoRAG:
    chunks = estado["chunks"]
    LIMIAR_RELEVANCIA = 0.4  # score do Qdrant tem escala diferente do rerank_score; ajuste testando
    estado["relevante"] = bool(chunks) and chunks[0]["score"] >= LIMIAR_RELEVANCIA
    return estado

@cronometrar("gerar_resposta")
def no_gerar_resposta(estado: EstadoRAG) -> EstadoRAG:
    trechos = _formatar_trechos(estado["chunks"])
    resp = llm_principal.invoke(PROMPT_GERAR_RESPOSTA.format(
        pergunta=estado["pergunta_original"], trechos=trechos
    ))
    estado["resposta"] = resp.content

    # Fontes deduplicadas, direto do front matter de cada markdown
    vistos = set()
    fontes = []
    numeros = _numerar_fontes(estado["chunks"])
    for c in estado["chunks"]:
        chave = _chave_fonte(c)
        if chave in vistos:
            continue
        vistos.add(chave)
        fontes.append({
            "numero": numeros[chave],
            "nome": c["titulo"],
            "url": c["fonte_url"],
            "referencia": c["caminho_hierarquico"] or c["artigo"],
        })
    estado["fontes"] = fontes
    return estado

@cronometrar("checar_fundamentacao")
def no_checar_fundamentacao(estado: EstadoRAG) -> EstadoRAG:
    if not estado["chunks"]:
        return estado
    trechos = _formatar_trechos(estado["chunks"])
    resp = llm_principal.invoke(PROMPT_CHECAR_FUNDAMENTACAO.format(
        trechos=trechos, resposta=estado["resposta"]
    ))
    estado["resposta"] = resp.content
    return estado

def no_resposta_nao_encontrada(estado: EstadoRAG) -> EstadoRAG:
    estado["resposta"] = (
        "Não encontrei informações suficientes na base documental para responder "
        "com segurança a essa pergunta. Recomendo consultar diretamente o edital "
        "correspondente ou a equipe responsável pela licitação."
    )
    estado["chunks"] = []
    return estado


def no_resposta_fora_escopo(estado: EstadoRAG) -> EstadoRAG:
    estado["resposta"] = (
        "Posso ajudar apenas com dúvidas relacionadas a licitações públicas "
        "(leis, decretos, editais, termos de referência etc.)."
    )
    estado["chunks"] = []
    return estado


# def no_checar_fundamentacao(estado: EstadoRAG) -> EstadoRAG:
#     if not estado["chunks"]:
#         return estado
#     trechos = _formatar_trechos(estado["chunks"])
#     resp = llm_principal.invoke(PROMPT_CHECAR_FUNDAMENTACAO.format(
#         trechos=trechos, resposta=estado["resposta"]
#     ))
#     estado["resposta"] = resp.content
#     estado["fontes"] = [
#         {"documento": c["documento"], "referencia": c["caminho_hierarquico"] or c["artigo"]}
#         for c in estado["chunks"]
#     ]
#     return estado


def _rota_apos_classificar(estado: EstadoRAG) -> str:
    return "reescrever" if estado["em_escopo"] else "fora_escopo"


def _rota_apos_avaliar(estado: EstadoRAG) -> str:
    if estado["relevante"]:
        return "gerar"
    if estado["tentativas"] >= MAX_LOOPS_REESCRITA:
        return "nao_encontrado"
    return "reescrever"


def construir_grafo():
    g = StateGraph(EstadoRAG)

    g.add_node("classificar", no_classificar)
    g.add_node("reescrever", no_reescrever)
    g.add_node("recuperar", no_recuperar)
    g.add_node("avaliar", no_avaliar_relevancia)
    g.add_node("gerar", no_gerar_resposta)
    g.add_node("checar", no_checar_fundamentacao)
    g.add_node("nao_encontrado", no_resposta_nao_encontrada)
    g.add_node("fora_escopo", no_resposta_fora_escopo)

    g.set_entry_point("classificar")

    g.add_conditional_edges("classificar", _rota_apos_classificar, {
        "reescrever": "reescrever",
        "fora_escopo": "fora_escopo",
    })

    g.add_edge("reescrever", "recuperar")
    g.add_edge("recuperar", "avaliar")

    g.add_conditional_edges("avaliar", _rota_apos_avaliar, {
        "gerar": "gerar",
        "reescrever": "reescrever",
        "nao_encontrado": "nao_encontrado",
    })

    g.add_edge("gerar", "checar")
    g.add_edge("checar", END)
    g.add_edge("nao_encontrado", END)
    g.add_edge("fora_escopo", END)

    return g.compile()


grafo_rag = construir_grafo()


def responder_pergunta(pergunta: str, historico: str = "") -> EstadoRAG:
    estado_inicial: EstadoRAG = {
        "pergunta_original": pergunta,
        "historico": historico,
        "tentativas": 0,
    }
    inicio_total = time.time()
    resultado = grafo_rag.invoke(estado_inicial)
    print(f"[TEMPO] TOTAL: {time.time() - inicio_total:.2f}s")
    return resultado


if __name__ == "__main__":
    resultado = responder_pergunta("Qual o prazo para impugnar um edital de pregão?")
    print(resultado["resposta"])
    print(resultado.get("fontes"))
