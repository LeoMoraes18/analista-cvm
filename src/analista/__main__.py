from analista.config import carregar_config
from analista.llm.cliente import conversar


def main() -> None:
    config = carregar_config()
    mensagens = [
        {"role": "system", "content": "Você é um analista de demonstrações financeiras. Responda em português."},
        {"role": "user", "content": "Em uma frase: o que é uma DRE?"},
    ]
    resposta = conversar(config, mensagens)
    print(resposta["content"])


if __name__ == "__main__":
    main()