"""Interface Gradio para testadores externos — substitui o streamlit_app.py
porque o Hugging Face Spaces no free tier não suporta mais SDK Streamlit
diretamente (só Static e Gradio sem custo; Docker/Streamlit exigem plano pago).

Rodar local: python ui/gradio_app.py
No HF Spaces: este arquivo é chamado pelo app.py da raiz (ver app.py).
"""
import re
import sys
import time
from pathlib import Path

# Garante que a raiz do projeto está no sys.path, mesmo rodando este arquivo
# diretamente ou a partir de outra pasta.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr
from app.main import responder

DISCLAIMER_TOPO = (
    "Pergunte, consulte as fontes e continue a conversa."
)


_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _citacoes_para_superscrito(texto: str) -> str:
    """Converte citações [1], [2], [3] ou [1, 2] em ¹,²,³."""
    def grupo(m):
        return ",".join(n.translate(_SUP) for n in re.findall(r"\d+", m.group(0)))
    bloco = r"\[\d+(?:\s*,\s*\d+)*\]"
    return re.sub(rf"{bloco}(?:\s*,?\s*{bloco})*", grupo, texto)


def _formatar_fontes_markdown(fontes: list[dict]) -> str:
    if not fontes:
        return "_Nenhuma fonte específica retornada para esta resposta._"
    linhas = []
    for i, f in enumerate(fontes, start=1):
        n = str(f.get("numero", i)).translate(_SUP)
        ref = f.get("referencia") or f["nome"]  # sem o nome do arquivo
        if f.get("url"):
            linhas.append(f"{n} {ref}  \n`{f['url']}`")
        else:
            linhas.append(f"{n} {ref}")
    return "\n\n".join(linhas)


def _bloco_fontes(fontes: list[dict]) -> str:
    """Bloco expansível 'Fontes consultadas' que fica dentro da própria resposta."""
    if not fontes:
        return ""
    return (
        "\n\n<details><summary><b>Fontes consultadas</b></summary>\n\n"
        + _formatar_fontes_markdown(fontes)
        + "\n\n</details>"
    )


CSS = """
#area-chat { position: relative; overflow: visible !important; }
#wrap-tema { position: fixed !important; top: 12px; right: 16px; height: 0; min-height: 0 !important;
    padding: 0 !important; margin: 0 !important; border: 0 !important; overflow: visible !important;
    z-index: 5; width: auto !important; background: transparent !important; }
#linha-tema { display: flex; justify-content: flex-end; padding: 0; margin: 0; }
#btn-tema {
    background: transparent; border: 1px solid var(--border-color-primary);
    border-radius: 8px; padding: 6px; cursor: pointer; color: inherit;
    display: inline-flex; align-items: center; justify-content: center;
}
#btn-tema:hover { background: var(--background-fill-secondary); }
/* Esconde o rodapé inteiro: Use via API, Built with Gradio e Settings */
footer { display: none !important; }
.digitando span {
    display: inline-block; width: 8px; height: 8px; margin: 0 2px;
    border-radius: 50%; background: currentColor; opacity: .3;
    animation: pulsar 1.2s infinite ease-in-out;
}
.digitando span:nth-child(2) { animation-delay: .2s; }
.digitando span:nth-child(3) { animation-delay: .4s; }
@keyframes pulsar { 0%, 80%, 100% { opacity: .3; } 40% { opacity: 1; } }
#caixa-chat.arrastando { outline: 2px dashed #3b82f6; outline-offset: 4px; border-radius: 8px; }
#caixa-chat.arrastando::after {
    content: "Solte o PDF ou DOCX aqui";
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
    background: rgba(59,130,246,.12); font-weight: 600; pointer-events: none;
}
#caixa-chat { position: relative; }
"""

# Aceita arrastar e soltar em qualquer ponto da caixa (conversa + pergunta):
# repassa os arquivos soltos ao <input type=file> do MultimodalTextbox.
JS_DRAG_DROP = """
() => {
    // Alternância de tema (o painel Settings do Gradio fica oculto)
    document.addEventListener('click', (e) => {
        if (e.target.closest && e.target.closest('#btn-tema')) {
            document.body.classList.toggle('dark');
        }
    });
    const caixa = () => document.getElementById('caixa-chat');
    const temArquivos = (e) => e.dataTransfer && Array.from(e.dataTransfer.types || []).includes('Files');
    document.addEventListener('dragover', (e) => {
        const c = caixa();
        if (c && c.contains(e.target) && temArquivos(e)) { e.preventDefault(); c.classList.add('arrastando'); }
    });
    document.addEventListener('dragleave', (e) => {
        const c = caixa();
        if (c && (!e.relatedTarget || !c.contains(e.relatedTarget))) c.classList.remove('arrastando');
    });
    document.addEventListener('drop', (e) => {
        const c = caixa();
        if (!c || !c.contains(e.target) || !temArquivos(e)) return;
        c.classList.remove('arrastando');
        const input = c.querySelector('input[type=file]');
        if (!input) return;
        e.preventDefault();
        e.stopPropagation();
        const dt = new DataTransfer();
        Array.from(e.dataTransfer.files).forEach((f) => {
            if (/\\.(pdf|docx)$/i.test(f.name)) dt.items.add(f);
        });
        if (!dt.files.length) return;
        input.files = dt.files;
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }, true);
}
"""

BOTAO_TEMA_HTML = (
    '<div id="linha-tema"><button id="btn-tema" type="button" title="Alternar tema" '
    'aria-label="Alternar tema claro/escuro">'
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="9"/><path d="M12 3v18" /><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/>'
    '</svg></button></div>'
)

ANIMACAO_ESPERA = (
    '<span class="digitando"><span></span><span></span><span></span></span>'
    " Consultando a base de licitações..."
)


def _historico_textual(historico: list[dict]) -> str:
    # remove o bloco de fontes (HTML) para não poluir o contexto do modelo
    limpo = lambda t: re.sub(r"<details>.*?</details>", "", t, flags=re.S).strip()
    return "\n".join(f"{h['role']}: {limpo(h['content'])}" for h in historico[-6:])


def _extrair_texto(caminho: str) -> str:
    """Extrai texto de PDF ou DOCX. Retorna '' se não houver texto (ex.: PDF escaneado)."""
    ext = Path(caminho).suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        leitor = PdfReader(caminho)
        return "\n".join((p.extract_text() or "") for p in leitor.pages).strip()
    if ext == ".docx":
        from docx import Document
        d = Document(caminho)
        partes = [p.text for p in d.paragraphs if p.text.strip()]
        for t in d.tables:
            for linha in t.rows:
                partes.append(" | ".join(c.text.strip() for c in linha.cells))
        return "\n".join(partes).strip()
    return ""


MAX_CHARS_POR_ARQUIVO = 4000
MAX_CHARS_TOTAL = 8000
PERGUNTA_PADRAO_ANEXO = (
    "Analise o documento anexado: em que etapa do processo de licitação estou "
    "e quais dúvidas posso ter a partir dele?"
)


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


def construir_app() -> gr.Blocks:
    with gr.Blocks(title="Licite Mais", css=CSS, js=JS_DRAG_DROP) as demo:
        gr.Markdown("# Seu assistente de licitações")
        gr.Markdown(DISCLAIMER_TOPO)

        with gr.Column(elem_id="area-chat"):
            # Botão de tema: fora do Group (que corta o overflow) e em posição absoluta,
            # então não ocupa espaço nem move os textos.
            gr.HTML(BOTAO_TEMA_HTML, elem_id="wrap-tema", padding=False)
            with gr.Group(elem_id="caixa-chat"):
                chatbot = gr.Chatbot(type="messages", height=500, show_label=False)
                docs_state = gr.State({})  # {nome_arquivo: texto} anexados nesta conversa
                entrada = gr.MultimodalTextbox(
                    placeholder="Digite sua pergunta ou anexe/arraste um PDF ou DOCX...",
                    show_label=False,
                    file_types=[".pdf", ".docx"],
                    file_count="multiple",
                    sources=["upload"],
                )
        botao_enviar = gr.Button("Enviar", variant="primary")

        def ao_enviar(valor, historico, docs):
            valor = valor or {}
            mensagem = (valor.get("text") or "").strip()
            arquivos = valor.get("files") or []
            if not mensagem and not arquivos:
                yield historico, None, docs
                return

            historico = historico or []
            docs = dict(docs or {})
            contexto = _historico_textual(historico)

            # Lê os anexos
            avisos, nomes = [], []
            for a in arquivos:
                caminho = a if isinstance(a, str) else a.get("path", "")
                nome = Path(caminho).name
                nomes.append(nome)
                try:
                    texto_doc = _extrair_texto(caminho)
                except Exception as e:
                    texto_doc = ""
                    avisos.append(f"Não consegui ler **{nome}** ({type(e).__name__}).")
                if texto_doc:
                    docs[nome] = texto_doc
                elif not any(nome in av for av in avisos):
                    avisos.append(f"**{nome}** não tem texto extraível (talvez seja um PDF escaneado).")

            # 1) Pergunta aparece já, com a animação de espera
            exibicao = mensagem or PERGUNTA_PADRAO_ANEXO
            if nomes:
                exibicao += "\n\n" + "\n".join(f"📎 {n}" for n in nomes)
            historico = historico + [
                {"role": "user", "content": exibicao},
                {"role": "assistant", "content": ANIMACAO_ESPERA},
            ]
            yield historico, None, docs

            # 2) Processa (bloqueante), enriquecendo a pergunta com os anexos
            pergunta = (mensagem or PERGUNTA_PADRAO_ANEXO) + _contexto_anexos(docs)
            resultado = responder(pergunta, historico=contexto)
            texto = _citacoes_para_superscrito(resultado["resposta"])

            # 3) Escreve progressivamente (efeito de digitação)
            partes = re.findall(r"\S+\s*", texto)
            acumulado = ""
            for i, parte in enumerate(partes, start=1):
                acumulado += parte
                if i % 3 == 0 or i == len(partes):
                    historico[-1] = {"role": "assistant", "content": acumulado}
                    yield historico, None, docs
                    time.sleep(0.03)

            # 4) Avisos de anexo + fontes em bloco expansível
            extra = ("\n\n⚠️ " + " ".join(avisos)) if avisos else ""
            historico[-1] = {
                "role": "assistant",
                "content": texto + extra + _bloco_fontes(resultado.get("fontes", [])),
            }
            yield historico, None, docs

        botao_enviar.click(ao_enviar, [entrada, chatbot, docs_state], [chatbot, entrada, docs_state])
        entrada.submit(ao_enviar, [entrada, chatbot, docs_state], [chatbot, entrada, docs_state])

    return demo


demo = construir_app()

if __name__ == "__main__":
    demo.launch(inbrowser=True, share=True, show_api=False)
