# Licite Mais

Chatbot RAG para ajudar partes interessadas de licitações (licitantes, pregoeiros,
equipe técnica/jurídica) a tirarem dúvidas sobre leis, decretos, editais e termos de referência.

**Stack:** LangChain · LangGraph · NeMo Guardrails · Qdrant · Gemini · Streamlit

## Arquitetura

- **Embeddings:** `BAAI/bge-m3` (multilíngue, bom em português)
- **Vector store:** Qdrant Cloud (free tier)
- **Reranker:** `BAAI/bge-reranker-v2-m3`
- **LLM:** Gemini 3.5 Flash Lite (geração) + Gemini 3.1 Flash-Lite (classificação/rails)
- **Orquestração:** LangGraph (classificar → reescrever → recuperar → rerank → avaliar
  relevância → gerar → checar fundamentação)
- **Guardrails:** NeMo Guardrails (escopo, jailbreak, PII, citação obrigatória, disclaimer)
- **UI de testes:** Streamlit
## Estrutura

```
rag-licitacao/
├── data/markdown/          # base de conhecimento
├── ingest/
│   ├── config.py           # configs centrais (modelos, paths, chunking)
│   ├── chunking.py         # markdown -> chunks com metadados
│   └── indexer.py          # embeddings + upload para o Qdrant
├── app/
│   ├── llm.py              # instâncias do Gemini
│   ├── prompts.py          # prompts do fluxo
│   ├── retriever.py        # busca no Qdrant
│   ├── reranker.py         # bge-reranker-v2-m3
│   ├── graph.py            # grafo LangGraph (fluxo completo)
│   ├── main.py             # junta guardrails + grafo
│   └── guardrails/         # config.yml, rails.co, actions.py
├── eval/
│   ├── dataset_exemplo.jsonl
│   └── evaluate.py         # avaliação com RAGAS
├── ui/
│   └── streamlit_app.py
├── requirements.txt
└── .env.example
```

## Passo a passo para começar

### 1. Ambiente
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Credenciais
```bash
cp .env.example .env
```
Preencha no `.env`:
- `GOOGLE_API_KEY` (AI Studio)
- `QDRANT_URL` e `QDRANT_API_KEY` (crie um cluster free em cloud.qdrant.io)

### 3. Dados
Coloque seus arquivos `.md` em `data/markdown/` (pode manter subpastas por tipo de norma).

Confira a heurística `inferir_tipo_documento()` em `ingest/chunking.py` — ajuste as
palavras-chave para bater com a nomenclatura real dos seus arquivos.

### 4. Indexação (rodar uma vez, e sempre que a base mudar)
```bash
python -m ingest.indexer
```

### 5. Testar o grafo isoladamente (sem UI)
```bash
python -m app.graph
```

### 6. Rodar a interface de testes
```bash
streamlit run ui/streamlit_app.py
```

### 7. Avaliação
Preencha `eval/dataset_exemplo.jsonl` com perguntas reais e respostas de referência, depois:
```bash
python -m eval.evaluate
```

### 8. Publicar para outras pessoas testarem
Opções gratuitas:
- **Streamlit Community Cloud** (mais simples: conecta no GitHub e sobe sozinho)
- **Hugging Face Spaces** (template Streamlit, CPU grátis)

Lembre de configurar as variáveis de ambiente (`GOOGLE_API_KEY`, `QDRANT_URL`,
`QDRANT_API_KEY`) como *secrets* na plataforma escolhida, nunca commitadas no repositório.

## Pontos ainda abertos (TODO)
- [ ] Busca híbrida real no Qdrant (hoje só denso; ver TODOs em `indexer.py`/`retriever.py`)
- [ ] Ajustar `inferir_tipo_documento()` para a nomenclatura real dos arquivos
- [ ] Preencher `eval/dataset_exemplo.jsonl` com perguntas e gabaritos reais
- [ ] Revisar a integração NeMo Guardrails ↔ LangGraph em `app/main.py` conforme a
      versão instalada das libs (a API deles muda com frequência)
- [ ] Testar limites de cota do Gemini com múltiplos usuários simultâneos no Streamlit
