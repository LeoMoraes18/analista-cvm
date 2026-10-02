from analista.agente.loop import executar_agente
from analista.config import carregar_config


def main() -> None:
    config = carregar_config()
    pergunta = (
        "A receita de uma empresa foi de 1.250.000 em 2023 e de 1.480.000 em 2024. "
        "O lucro líquido de 2024 foi de 162.800. "
        "Qual foi o crescimento da receita e qual a margem líquida de 2024?"
    )
    print(executar_agente(config, pergunta))


if __name__ == "__main__":
    main()