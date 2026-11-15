"""Interface simples em Streamlit para testadores externos.
Rodar com: streamlit run ui/streamlit_app.py (a partir da RAIZ do projeto)
"""
import sys
from pathlib import Path

# O Streamlit coloca a pasta deste script (ui/) no sys.path, não a raiz do
# projeto — por isso "import app.xxx" falha com ModuleNotFoundError mesmo
# rodando o comando a partir da raiz. Esta linha resolve isso em qualquer SO.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from app.main import responder

st.set_page_config(page_title="Licite Mais")
st.header("Seu assistente de licitações")
st.caption("Pergunte, consulte as fontes e entenda as leis.")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []


def _renderizar_fontes(fontes: list[dict]):
    """Mostra a lista de fontes com nome oficial + link clicável (quando houver),
    sem nunca expor o nome do arquivo .md.
    """
    if not fontes:
        st.caption("Nenhuma fonte específica retornada para esta resposta.")
        return
    for f in fontes:
        if f.get("url"):
            st.markdown(f"- [{f['nome']}]({f['url']}) — {f['referencia']}")
        else:
            st.markdown(f"- **{f['nome']}** — {f['referencia']}")


for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("fontes"):
            with st.expander("Fontes consultadas"):
                _renderizar_fontes(msg["fontes"])

pergunta = st.chat_input("Digite sua pergunta sobre a licitação...")

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando a base documental..."):
            historico_textual = "\n".join(
                f"{m['role']}: {m['content']}" for m in st.session_state.mensagens[-6:]
            )
            resultado = responder(pergunta, historico=historico_textual)

        st.markdown(resultado["resposta"])
        if resultado.get("fontes"):
            with st.expander("Fontes consultadas"):
                _renderizar_fontes(resultado["fontes"])

    st.session_state.mensagens.append({
        "role": "assistant",
        "content": resultado["resposta"],
        "fontes": resultado.get("fontes", []),
    })