"""Interface simples em Streamlit para testadores externos.
Rodar com: streamlit run ui/streamlit_app.py (a partir da RAIZ do projeto)
"""
import re
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


_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _citacoes_para_superscrito(texto: str) -> str:
    """Converte citações [1], [2], [3] ou [1, 2] em ¹,²,³."""
    def grupo(m):
        return ",".join(n.translate(_SUP) for n in re.findall(r"\d+", m.group(0)))
    bloco = r"\[\d+(?:\s*,\s*\d+)*\]"
    return re.sub(rf"{bloco}(?:\s*,?\s*{bloco})*", grupo, texto)


def _renderizar_fontes(fontes: list[dict]):
    """Mostra a lista de fontes numeradas + link clicável (quando houver),
    sem expor o nome do arquivo .md.
    """
    if not fontes:
        st.caption("Nenhuma fonte específica retornada para esta resposta.")
        return
    for i, f in enumerate(fontes, start=1):
        n = f.get("numero", i)
        ref = f.get("referencia") or f["nome"]
        if f.get("url"):
            st.markdown(f"**{n}.** [{ref}]({f['url']})")
        else:
            st.markdown(f"**{n}.** {ref}")


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

        resposta_formatada = _citacoes_para_superscrito(resultado["resposta"])
        st.markdown(resposta_formatada)
        if resultado.get("fontes"):
            with st.expander("Fontes consultadas"):
                _renderizar_fontes(resultado["fontes"])

    st.session_state.mensagens.append({
        "role": "assistant",
        "content": resposta_formatada,
        "fontes": resultado.get("fontes", []),
    })