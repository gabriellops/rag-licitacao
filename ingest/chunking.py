"""Transforma os arquivos .md em chunks com metadados prontos para citação.

Estratégia:
1. MarkdownHeaderTextSplitter -> preserva Título > Capítulo > Seção > Artigo
2. RecursiveCharacterTextSplitter -> só aplicado em blocos que ainda ficarem grandes
3. Prefixa o caminho hierárquico ao texto antes de embedar (dá contexto ao embedding)
4. Gera metadados: documento, tipo, caminho_hierarquico, artigo, arquivo_origem
"""
import os
import yaml
from pathlib import Path
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from ingest.config import MARKDOWN_DIR, MD_HEADERS_TO_SPLIT, CHUNK_SIZE, CHUNK_OVERLAP


def inferir_tipo_documento(nome_arquivo: str) -> str:
    """Heurística simples para classificar o tipo de norma/documento pelo nome do arquivo.
    Ajuste as palavras-chave conforme a nomenclatura real da sua base.
    """
    nome = nome_arquivo.lower()
    if "lei" in nome:
        return "lei"
    if "decreto" in nome:
        return "decreto"
    if "edital" in nome:
        return "edital"
    if any(k in nome for k in ["tr", "termo_de_referencia", "termo-de-referencia"]):
        return "termo_de_referencia"
    if "ata" in nome:
        return "ata"
    if "faq" in nome:
        return "faq"
    return "outro"


def carregar_markdowns(diretorio: str = MARKDOWN_DIR) -> list[tuple[str, str]]:
    """Retorna lista de (caminho_arquivo, conteudo_bruto)."""
    arquivos = []
    for path in Path(diretorio).rglob("*.md"):
        texto = path.read_text(encoding="utf-8")
        arquivos.append((str(path), texto))
    return arquivos

def extrair_frontmatter(conteudo: str) -> tuple[dict, str]:
    """Separa o front matter YAML (entre --- ---) do corpo do markdown.
    Retorna (metadados_frontmatter, conteudo_sem_frontmatter).
    """
    if conteudo.startswith("---"):
        partes = conteudo.split("---", 2)
        if len(partes) >= 3:
            try:
                frontmatter = yaml.safe_load(partes[1]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            corpo = partes[2].lstrip("\n")
            return frontmatter, corpo
    return {}, conteudo

def chunk_documento(caminho_arquivo: str, conteudo: str) -> list[Document]:
    """Aplica o split hierárquico + fallback recursivo e devolve Documents com metadados."""
    frontmatter, conteudo = extrair_frontmatter(conteudo)

    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=MD_HEADERS_TO_SPLIT)
    blocos = header_splitter.split_text(conteudo)

    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    nome_arquivo = os.path.basename(caminho_arquivo)
    # Prioriza o front matter; cai na heurística pelo nome só se o .md não tiver front matter
    titulo_oficial = frontmatter.get("titulo", nome_arquivo)
    tipo_doc = (frontmatter.get("tipo") or inferir_tipo_documento(nome_arquivo)).lower()
    fonte_url = frontmatter.get("fonte", "")
    numero = frontmatter.get("numero", "")
    data_norma = str(frontmatter.get("data", ""))
    revogada = frontmatter.get("revogada", False)

    chunks_finais: list[Document] = []
    for bloco in blocos:
        # Monta o caminho hierárquico (ex: "Lei 14.133/2021 > Título II > Art. 75")
        partes_hierarquia = [v for v in bloco.metadata.values() if v]
        caminho_hierarquico = " > ".join(partes_hierarquia)

        texto_com_contexto = f"{caminho_hierarquico}\n\n{bloco.page_content}" if caminho_hierarquico else bloco.page_content

        sub_blocos = fallback_splitter.split_text(bloco.page_content)
        for sub in sub_blocos:
            metadata = {
                "documento": nome_arquivo,
                "titulo": titulo_oficial,
                "tipo": tipo_doc,
                "numero": numero,
                "data_norma": data_norma,
                "revogada": revogada,
                "fonte_url": fonte_url,
                "caminho_hierarquico": caminho_hierarquico,
                "artigo": bloco.metadata.get("artigo", ""),
                "arquivo_origem": caminho_arquivo,
            }
            texto_final = f"{caminho_hierarquico}\n\n{sub}" if caminho_hierarquico else sub
            chunks_finais.append(Document(page_content=texto_final, metadata=metadata))

    return chunks_finais


def processar_toda_base(diretorio: str = MARKDOWN_DIR) -> list[Document]:
    todos_chunks: list[Document] = []
    for caminho, conteudo in carregar_markdowns(diretorio):
        todos_chunks.extend(chunk_documento(caminho, conteudo))
    return todos_chunks


if __name__ == "__main__":
    chunks = processar_toda_base()
    print(f"Total de chunks gerados: {len(chunks)}")
    if chunks:
        print("--- Exemplo ---")
        print(chunks[0].metadata)
        print(chunks[0].page_content[:300])
