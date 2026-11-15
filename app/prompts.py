"""Prompts centralizados. Ajuste o tom/termos conforme o órgão/edital específico."""

PROMPT_CLASSIFICAR = """Classifique a pergunta abaixo em uma das categorias:
- "licitacao": dúvida sobre lei, decreto, edital, termo de referência, prazos, impugnação, recursos etc.
- "fora_escopo": qualquer outro assunto.

Pergunta: {pergunta}

Responda apenas com uma palavra: licitacao ou fora_escopo."""

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

PROMPT_GERAR_RESPOSTA = """Você é um assistente especializado em licitações públicas (Lei 14.133/2021 e normas correlatas).
Responda à pergunta das partes interessadas usando SOMENTE as informações dos trechos fornecidos.
Regras:
- Cite cada afirmação usando o número de referência entre colchetes do trecho correspondente, ex: [1], [2].
- Coloque a citação logo após a afirmação que ela sustenta, citando só o(s) trecho(s) que realmente a embasam. NÃO agrupe todas as citações no fim do parágrafo e NÃO cite todos os trechos de uma vez.
- NUNCA mencione nome de arquivo, extensão .md ou caminho de arquivo na resposta.
- Se os trechos não cobrirem a pergunta, diga claramente que não encontrou a informação na base.
- Não invente números de artigo, prazos ou valores.

Pergunta: {pergunta}

Trechos disponíveis:
{trechos}

Resposta (use apenas [1], [2]... para citar, sem nomes de arquivo):"""

PROMPT_CHECAR_FUNDAMENTACAO = """Você vai revisar uma resposta já pronta, comparando com os trechos fornecidos.
Responda APENAS com a resposta final, sem nenhum comentário sobre o processo de verificação,
sem frases como "a resposta está apoiada" ou "após verificar". Comece direto pelo conteúdo da resposta.

Regras da revisão:
- Se alguma afirmação não tiver apoio claro nos trechos, remova ou suavize essa afirmação.
- Mantenha as citações numéricas [1], [2]... exatamente como estão.
- NUNCA mencione nome de arquivo.
- Não adicione nenhuma introdução, conclusão ou comentário sobre a verificação em si.

Trechos:
{trechos}

Resposta a revisar:
{resposta}

Resposta final (só o conteúdo, sem comentários):"""
