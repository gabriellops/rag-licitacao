"""Avaliação do RAG com RAGAS.
Métricas: faithfulness (fidelidade aos trechos), answer_relevancy, context_precision/recall.

Rodar: python -m eval.evaluate
Pré-requisito: preencher eval/dataset_exemplo.jsonl com perguntas e respostas de referência reais
(ou renomear para dataset.jsonl).
"""
import json
from pathlib import Path

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

from app.graph import responder_pergunta

DATASET_PATH = Path(__file__).parent / "dataset_exemplo.jsonl"


def carregar_dataset(path: Path = DATASET_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def rodar_avaliacao():
    itens = carregar_dataset()

    perguntas, respostas, contextos, referencias = [], [], [], []

    for item in itens:
        estado = responder_pergunta(item["pergunta"])
        perguntas.append(item["pergunta"])
        respostas.append(estado["resposta"])
        contextos.append([c["texto"] for c in estado.get("chunks", [])])
        referencias.append(item["resposta_esperada"])

    dataset = Dataset.from_dict({
        "question": perguntas,
        "answer": respostas,
        "contexts": contextos,
        "ground_truth": referencias,
    })

    resultado = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    print(resultado)
    resultado.to_pandas().to_csv("eval/resultados.csv", index=False)
    print("Resultados salvos em eval/resultados.csv")


if __name__ == "__main__":
    rodar_avaliacao()
