"""Roda perguntas com resposta conhecida e mostra o placar do modelo configurado."""

import sys
import time
from collections import Counter
from dataclasses import dataclass

from analista.agente.loop import Execucao, executar_agente
from analista.banco import conectar
from analista.config import carregar_config


@dataclass(frozen=True)
class Caso:
    pergunta: str
    ferramentas: tuple[str, ...]  # precisam ter sido chamadas
    trechos: tuple[str, ...]  # precisam aparecer na resposta


CASOS = [
    Caso(
        "Qual foi a margem líquida da Petrobras em 2024?",
        ("buscar_empresa", "obter_contas", "margem"),
        ("7,54",),
    ),
    Caso(
        "Qual foi a margem líquida da Petrobras em 2022?",
        ("buscar_empresa", "obter_contas", "margem"),
        ("29,47",),
    ),
    Caso(
        "Quanto a receita da Petrobras variou de 2022 para 2023?",
        ("buscar_empresa", "obter_contas", "variacao_percentual"),
        ("20,16",),
    ),
    Caso(
        "Quanto o lucro da Petrobras variou de 2023 para 2024?",
        ("buscar_empresa", "obter_contas", "variacao_percentual"),
        ("70,43",),
    ),
    Caso(
        "Qual foi a receita da Automob em 2023?",
        ("buscar_empresa", "obter_contas"),
        ("AUTOMOB S.A.", "AUTOMOB PARTICIPAÇÕES"),
    ),
    Caso(
        "Qual foi o lucro da Bradsaúde em 2023?",
        ("buscar_empresa", "obter_contas"),
        ("inconsist",),
    ),
    Caso(
        "Qual o código CVM da empresa Xablau Tecnologia?",
        ("buscar_empresa",),
        ("não",),
    ),
]


def normalizar(texto: str) -> str:
    return texto.replace(".", ",").casefold()


def falhas(caso: Caso, execucao: Execucao) -> list[str]:
    chamadas = {c.nome for c in execucao.chamadas}
    resposta = normalizar(execucao.resposta)
    problemas = [f"não chamou {f}" for f in caso.ferramentas if f not in chamadas]
    problemas += [f"resposta sem '{t}'" for t in caso.trechos if normalizar(t) not in resposta]
    return problemas


def main() -> None:
    config = carregar_config()
    repeticoes = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    acertos = 0
    inicio = time.perf_counter()

    with conectar(config) as conexao:
        for caso in CASOS:
            problemas: Counter[str] = Counter()
            certos = 0
            for _ in range(repeticoes):
                try:
                    encontrados = falhas(caso, executar_agente(config, conexao, caso.pergunta))
                except Exception as erro:
                    encontrados = [f"erro: {type(erro).__name__}: {erro}"]
                if encontrados:
                    problemas.update(encontrados)
                else:
                    certos += 1
            acertos += certos
            print(f"{certos}/{repeticoes}  {caso.pergunta}")
            for problema, vezes in problemas.items():
                print(f"       {vezes}x {problema}")

    total = len(CASOS) * repeticoes
    duracao = time.perf_counter() - inicio
    print(f"\n{config.llm_modelo}: {acertos}/{total} ({acertos / total:.0%}) em {duracao:.0f}s")


if __name__ == "__main__":
    main()