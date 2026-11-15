# Licite Mais

O Licite Mais é um chatbot de perguntas e respostas sobre licitações públicas no Brasil. A ideia é ajudar quem participa de pregões e contratações (licitantes, pregoeiros ou equipe técnica) a tirar dúvidas direto na legislação, sem precisar garimpar dezenas de páginas de lei.

Ele consulta uma base de normas já indexada (como a Lei nº 14.133/2021, decretos, instruções normativas e o FAQ do PNCP) e devolve a resposta com as citações numeradas e os links para as fontes originais. Se a base interna não cobrir a dúvida, o sistema faz uma busca na web para tentar responder. Também dá para anexar arquivos PDF ou DOCX direto no chat para contextualizar a pergunta.

## O que foi usado

O projeto roda em Python. A interface principal usa Streamlit (`ui/streamlit_app.py`), e há também uma versão alternativa em Gradio (`ui/gradio_app.py`).

Para o fluxo de conversa e busca, usei LangGraph e LangChain (`app/graph.py`), que coordenam saudação, checagem de escopo, reescrita de pergunta, recuperação de trechos e fallback na web. Os modelos de linguagem são da família Gemini: `gemini-3.5-flash-lite` gera as respostas e `gemini-3.1-flash-lite` cuida da classificação e da reescrita.

Os arquivos Markdown de `data/markdown/` são divididos por hierarquia (`ingest/chunking.py`), vetorizados com `BAAI/bge-m3` e salvos no Qdrant Cloud. O repositório inclui um reranker (`BAAI/bge-reranker-v2-m3` em `app/reranker.py`), mas ele fica desativado por padrão no grafo para manter as respostas rápidas em CPU.

Na camada de segurança e fontes extras, o NeMo Guardrails (`app/guardrails/`) bloqueia assuntos fora de escopo, tentativas de burlar instruções, envio de CPF/RG na pergunta e garante o aviso de que a resposta não substitui parecer jurídico. Quando a base local não cobre a pergunta, entra a busca na web com Tavily (`app/busca_web.py`). Para anexos enviados no chat, `pypdf` e `python-docx` extraem o texto direto em memória. Há ainda um script de avaliação com RAGAS em `eval/evaluate.py`.

## Estrutura do projeto

```text
rag-licitacao/
├── app/
│   ├── busca_web.py      # fallback na web com Tavily
│   ├── graph.py          # fluxo principal no LangGraph
│   ├── llm.py            # instâncias do Gemini
│   ├── main.py           # junta guardrails de entrada/saída e o grafo
│   ├── prompts.py        # prompts do sistema
│   ├── reranker.py       # reranker opcional (bge-reranker-v2-m3)
│   ├── retriever.py      # busca vetorial no Qdrant
│   └── guardrails/       # regras e ações do NeMo Guardrails
├── data/markdown/        # leis, decretos, INs e FAQs em Markdown
├── eval/                 # dataset de exemplo e script de avaliação (RAGAS)
├── ingest/
│   ├── chunking.py       # quebra os arquivos .md preservando título e artigo
│   ├── config.py         # variáveis de ambiente, modelos e parâmetros
│   └── indexer.py        # gera embeddings e envia os chunks para o Qdrant
├── ui/
│   ├── streamlit_app.py  # interface principal em Streamlit
│   └── gradio_app.py     # interface alternativa em Gradio
├── app.py                # entrypoint para rodar o Gradio (ex.: Hugging Face Spaces)
└── requirements.txt      # dependências Python
```

## Como baixar e rodar no seu computador

### 1. Pré-requisitos

Você vai precisar de:

- Python 3.11 ou 3.12 instalado
- Git
- Uma chave de API do Google AI Studio (para o Gemini)
- Uma conta gratuita no Qdrant Cloud (para armazenar e buscar os vetores)
- Opcional: uma chave da API do Tavily, caso queira ativar o fallback de busca na web

### 2. Clonar o repositório e instalar as dependências

Abra o terminal e baixe o projeto:

```bash
git clone https://github.com/gabriellops/rag-licitacao.git
cd rag-licitacao
```

Crie e ative um ambiente virtual:

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Instale as bibliotecas do projeto e o Streamlit (que não vem listado no `requirements.txt` porque o Streamlit Cloud já o instala automaticamente):

```bash
pip install -r requirements.txt
pip install streamlit
```

### 3. Configurar as chaves de acesso

Crie um arquivo chamado `.env` na raiz da pasta `rag-licitacao` com o conteúdo abaixo e preencha suas chaves:

```env
GOOGLE_API_KEY=sua_chave_do_google_ai_studio
QDRANT_URL=https://seu-cluster.qdrant.io:6333
QDRANT_API_KEY=sua_chave_do_qdrant
QDRANT_COLLECTION=licitacao_rag

# Opcional (necessário apenas para o fallback de busca na web)
TAVILY_API_KEY=sua_chave_do_tavily
```

Nunca envie o arquivo `.env` para o GitHub (ele já está listado no `.gitignore`).

### 4. Indexar os documentos no Qdrant

Antes de usar o chat pela primeira vez, você precisa enviar os arquivos de `data/markdown/` para o seu cluster no Qdrant. Na primeira execução, o Python vai baixar o modelo `BAAI/bge-m3` automaticamente:

```bash
python -m ingest.indexer
```

Você só precisa rodar esse comando novamente se adicionar ou alterar arquivos na pasta `data/markdown/`.

### 5. Abrir o chatbot

Com tudo configurado e indexado, inicie a interface do Streamlit:

```bash
streamlit run ui/streamlit_app.py
```

O navegador deve abrir automaticamente no endereço local (normalmente `http://localhost:8501`).

Se quiser testar apenas o fluxo no terminal, sem abrir interface visual, rode:

```bash
python -m app.graph
```
