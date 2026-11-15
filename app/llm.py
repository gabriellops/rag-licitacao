"""Instâncias do Gemini usadas no grafo.
- llm_principal: geração da resposta final (mais capaz)
- llm_rapido: classificação, reescrita de consulta, checagens (mais barato/rápido)
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from ingest.config import GEMINI_MODEL, GEMINI_MODEL_LITE

llm_principal = ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0.25)
llm_rapido = ChatGoogleGenerativeAI(model=GEMINI_MODEL_LITE, temperature=0)
