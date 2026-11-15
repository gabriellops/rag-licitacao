"""Prompts centralizados. Ajuste o tom/termos conforme o órgão/edital específico."""

PROMPT_CLASSIFICAR = """Classifique a mensagem abaixo em uma das categorias:
- "saudacao": cumprimentos e saudações simples sem pergunta técnica (ex: oi, olá, bom dia, boa tarde, boa noite, tudo bem, e aí, opa).
- "licitacao": dúvida sobre lei, decreto, edital, termo de referência, prazos, impugnação, recursos, análise de documento anexado etc.
- "fora_escopo": qualquer outro assunto.

Mensagem: {pergunta}

Responda apenas com uma palavra: saudacao, licitacao ou fora_escopo."""

PROMPT_REESCREVER = """Reescreva a pergunta abaixo como uma consulta de busca objetiva,
mantendo os termos técnicos e números de artigo/lei citados. Não responda a pergunta.

Pergunta original: {pergunta}
Histórico relevante (se houver): {historico}

Consulta reescrita:"""

PROMPT_AVALIAR_RELEVANCIA = """Os trechos abaixo são suficientes para responder à pergunta com segurança?
Responda apenas "sim" ou "nao".

Pergunta: {pergunta}

Trechos recuperados:
{trechos}
"""

PROMPT_GERAR_RESPOSTA = """Você é o Licite Mais, um especialista em licitações públicas (Lei 14.133/2021 e normas correlatas).
Converse de forma humana, clara, acolhedora e direta, traduzindo termos jurídicos para uma linguagem acessível a quem participa de licitações.

Como responder:
- Vá direto ao ponto com naturalidade. NUNCA comece com frases robóticas como "Com base nos trechos fornecidos", "De acordo com os trechos disponíveis" ou "Segundo os documentos apresentados".
- Explique de forma didática: use parágrafos curtos e listas com marcadores quando houver requisitos, documentos ou etapas.
- Use SOMENTE as informações das fontes fornecidas abaixo, sem inventar números de artigo, prazos ou valores.
- Cite cada afirmação usando o número da fonte entre colchetes, ex: [1], [2], logo após a frase ou item que ela sustenta. NÃO agrupe todas as citações no fim do parágrafo e NÃO cite fontes que não embasam aquela frase.
- Se alguma fonte tiver `origem="web"`, deixe claro de forma natural que aquela informação veio de uma fonte externa na web (não da legislação oficial indexada) e recomende conferir o link.
- NUNCA mencione nome de arquivo, extensão .md ou caminho de arquivo na resposta.
- Se as fontes não cobrirem parte da pergunta, diga isso com transparência e oriente o próximo passo prático (ex: consultar o edital ou o órgão licitante).

Histórico recente da conversa (se houver):
{historico}

Pergunta atual: {pergunta}

Fontes disponíveis:
{trechos}

Resposta natural e objetiva (cite com [1], [2]... sem nomes de arquivo):"""

PROMPT_CHECAR_FUNDAMENTACAO = """Você vai revisar uma resposta já pronta, comparando-a com as fontes fornecidas.
Responda APENAS com a resposta final, sem nenhum comentário sobre a verificação,
sem frases como "a resposta está apoiada" ou "após verificar". Comece direto pelo conteúdo da resposta.

Regras da revisão:
- Preserve o tom humano, claro, natural e conversacional da resposta; não a deixe seca ou robótica.
- Se alguma afirmação, prazo, valor ou artigo não tiver apoio claro nas fontes, remova ou suavize essa afirmação.
- Mantenha as citações numéricas [1], [2]... exatamente como estão (e no lugar certo).
- NUNCA mencione nome de arquivo.
- Não adicione introdução, conclusão ou comentário sobre a revisão em si.

Fontes:
{trechos}

Resposta a revisar:
{resposta}

Resposta final (só o conteúdo, sem comentários):"""
