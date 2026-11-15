"""Orquestra: rail de entrada (NeMo) -> grafo LangGraph -> rail de saída (NeMo).

TODO: a integração "ideal" entre NeMo Guardrails e LangGraph varia bastante de versão
para versão das duas libs. Esta função assume o uso de `rails.generate_async` apenas
para os rails de ENTRADA (bloquear antes de gastar chamadas no grafo) e aplica os
rails de SAÍDA manualmente sobre o texto final, via `rails.generate_async` novamente
com uma mensagem "fake" contendo a resposta do grafo. Ajuste conforme testar a versão
instalada do nemoguardrails.
"""
import asyncio
from app.graph import responder_pergunta
from app.guardrails import rails


async def processar_mensagem(pergunta_usuario: str, historico: str = "") -> dict:
    # 1) Rail de entrada: pode interromper aqui (fora de escopo, jailbreak, PII)
    resposta_rail_entrada = await rails.generate_async(messages=[
        {"role": "user", "content": pergunta_usuario}
    ])
    texto_rail_entrada = resposta_rail_entrada.get("content", "")

    # Heurística simples: se o rail já devolveu uma recusa padrão, paramos por aqui.
    recusas_conhecidas = ["Posso ajudar apenas", "Não posso ignorar", "evite incluir CPF"]
    if any(r in texto_rail_entrada for r in recusas_conhecidas):
        return {"resposta": texto_rail_entrada, "fontes": []}

    # 2) Grafo RAG
    estado_final = responder_pergunta(pergunta_usuario, historico=historico)
    resposta_bruta = estado_final["resposta"]

    if estado_final.get("categoria") in ("saudacao", "fora_escopo"):
        return {"resposta": resposta_bruta, "fontes": []}

    # 3) Rail de saída: aplica checagens de citação/disclaimer sobre a resposta do grafo
    #    (implementação simplificada chamando as actions diretamente)
    from app.guardrails import actions
    if not await actions.verificar_disclaimer(resposta_bruta):
        resposta_bruta = await actions.adicionar_disclaimer(resposta_bruta)
    if not await actions.verificar_citacao(resposta_bruta):
        resposta_bruta = await actions.adicionar_aviso_sem_citacao(resposta_bruta)

    return {"resposta": resposta_bruta, "fontes": estado_final.get("fontes", [])}


def responder(pergunta_usuario: str, historico: str = "") -> dict:
    """Wrapper síncrono, conveniente para a UI Streamlit."""
    return asyncio.run(processar_mensagem(pergunta_usuario, historico))


if __name__ == "__main__":
    resultado = responder("Qual o prazo para impugnar um edital de pregão?")
    print(resultado["resposta"])
    print(resultado["fontes"])
