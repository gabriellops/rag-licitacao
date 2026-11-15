"""Interface simples em Streamlit para testadores externos.
Rodar com: streamlit run ui/streamlit_app.py (a partir da RAIZ do projeto)
"""
import io
import re
import sys
import time
from pathlib import Path

# O Streamlit coloca a pasta deste script (ui/) no sys.path, não a raiz do
# projeto — por isso "import app.xxx" falha com ModuleNotFoundError mesmo
# rodando o comando a partir da raiz. Esta linha resolve isso em qualquer SO.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from app.main import responder

st.set_page_config(page_title="Licite Mais")
st.markdown(
    """
    <style>
    /* Remove os ícones de usuário e robô */
    [data-testid^="stChatMessageAvatar"] { display: none !important; }
    /* Mensagem do assistente à esquerda */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        margin-right: auto; max-width: 85%; width: fit-content;
        border-radius: 14px; padding: 0.65rem 1rem;
    }
    /* Mensagem do usuário à direita */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        margin-left: auto; max-width: 78%; width: fit-content;
        border-radius: 14px; padding: 0.65rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.header("Seu assistente de licitações")
st.caption("Pergunte, consulte as fontes e entenda as leis.")

MENSAGEM_INICIAL = (
    "Olá! Sou seu assistente virtual especializado em licitações e contratos públicos. "
    "Como posso ajudar?"
)
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [{"role": "assistant", "content": MENSAGEM_INICIAL}]
if "docs" not in st.session_state:
    st.session_state.docs = {}

MAX_CHARS_POR_ARQUIVO = 4000
MAX_CHARS_TOTAL = 8000
PERGUNTA_PADRAO_ANEXO = (
    "Analise o documento anexado: em que etapa do processo de licitação estou "
    "e quais dúvidas posso ter a partir dele?"
)


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
        rotulo = "🌐 " if f.get("fonte_tipo") == "web" else ""
        if f.get("url"):
            st.markdown(f"**{n}.** {rotulo}[{ref}]({f['url']})")
        else:
            st.markdown(f"**{n}.** {rotulo}{ref}")


def _extrair_texto_bytes(nome: str, dados: bytes) -> str:
    """Extrai texto de PDF ou DOCX em memória. Retorna '' se não houver texto."""
    ext = Path(nome).suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        leitor = PdfReader(io.BytesIO(dados))
        return "\n".join((p.extract_text() or "") for p in leitor.pages).strip()
    if ext == ".docx":
        from docx import Document
        d = Document(io.BytesIO(dados))
        partes = [p.text for p in d.paragraphs if p.text.strip()]
        for t in d.tables:
            for linha in t.rows:
                partes.append(" | ".join(c.text.strip() for c in linha.cells))
        return "\n".join(partes).strip()
    return ""


def _contexto_anexos(docs: dict) -> str:
    if not docs:
        return ""
    blocos, total = [], 0
    for nome, texto in docs.items():
        trecho = texto[:MAX_CHARS_POR_ARQUIVO][: max(0, MAX_CHARS_TOTAL - total)]
        if not trecho:
            break
        total += len(trecho)
        blocos.append(f"--- {nome} ---\n{trecho}")
    return (
        "\n\n[Contexto extraído de documento(s) anexado(s) pelo usuário. Use-o apenas "
        "para entender em que etapa ele está e quais são suas dúvidas; a resposta deve "
        "se basear nos trechos da base legal.]\n" + "\n\n".join(blocos)
    )


def _stream_texto(texto: str):
    """Gera palavras aos poucos para efeito de digitação no st.write_stream."""
    for parte in re.findall(r"\S+\s*", texto):
        yield parte
        time.sleep(0.02)


for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("fontes"):
            with st.expander("Fontes consultadas"):
                _renderizar_fontes(msg["fontes"])

entrada = st.chat_input(
    "Digite sua pergunta ou anexe/arraste um PDF ou DOCX...",
    accept_file="multiple",
    file_type=["pdf", "docx"],
)

if entrada:
    texto_usuario = (entrada.text or "").strip() if hasattr(entrada, "text") else str(entrada).strip()
    arquivos = list(entrada.files or []) if hasattr(entrada, "files") else []

    if texto_usuario or arquivos:
        avisos, nomes = [], []
        for arq in arquivos:
            nomes.append(arq.name)
            try:
                texto_doc = _extrair_texto_bytes(arq.name, arq.getvalue())
            except Exception as e:
                texto_doc = ""
                avisos.append(f"Não consegui ler **{arq.name}** ({type(e).__name__}).")
            if texto_doc:
                st.session_state.docs[arq.name] = texto_doc
            elif not any(arq.name in av for av in avisos):
                avisos.append(f"**{arq.name}** não tem texto extraível (talvez seja um PDF escaneado).")

        exibicao = texto_usuario or PERGUNTA_PADRAO_ANEXO
        if nomes:
            exibicao += "\n\n" + "\n".join(f"📎 {n}" for n in nomes)

        historico_textual = "\n".join(
            f"{m['role']}: {m['content']}" for m in st.session_state.mensagens[-6:]
        )
        st.session_state.mensagens.append({"role": "user", "content": exibicao})
        with st.chat_message("user"):
            st.markdown(exibicao)

        pergunta_enriquecida = (texto_usuario or PERGUNTA_PADRAO_ANEXO) + _contexto_anexos(st.session_state.docs)

        with st.chat_message("assistant"):
            with st.spinner("Consultando a base documental..."):
                resultado = responder(pergunta_enriquecida, historico=historico_textual)

            resposta_formatada = _citacoes_para_superscrito(resultado["resposta"])
            st.write_stream(_stream_texto(resposta_formatada))
            if avisos:
                st.warning(" ".join(avisos))
            if resultado.get("fontes"):
                with st.expander("Fontes consultadas"):
                    _renderizar_fontes(resultado["fontes"])

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": resposta_formatada,
            "fontes": resultado.get("fontes", []),
        })