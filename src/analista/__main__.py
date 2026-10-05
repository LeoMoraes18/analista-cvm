from analista.agente.loop import executar_agente, Execucao
from analista.banco import conectar, criar_esquema
from analista.carga.carregar import garantir_carga
from analista.config import carregar_config


PERGUNTAS = [
    "Qual foi a margem líquida da Petrobras em 2024?",
    "Quanto a receita da Petrobras variou de 2022 para 2023?",
    "Qual foi a receita da Automob em 2023?",
]

def main() -> None:
    config = carregar_config()

    with conectar(config) as conexao:
        criar_esquema(conexao)
        garantir_carga(conexao)
        for pergunta in PERGUNTAS:
            print(f"\n> {pergunta}")
            execucao = executar_agente(config, conexao, pergunta)
            for c in execucao.chamadas:
                resumo = c.resultado if len(c.resultado) <= 120 else c.resultado[:117] + "..."
                print(f"   [ferramenta] {c.nome}({c.argumentos}) -> {resumo}")
            print(execucao.resposta)

if __name__ == "__main__":
    main()