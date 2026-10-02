from analista.agente.ferramentas import DESCRICOES, executar
from analista.config import Config
from analista.llm.cliente import conversar

MAX_PASSOS = 8

INSTRUCOES = (
    "Você é um analista de demonstrações financeiras. Responda em português. "
    "Nunca faça contas de cabeça: use as ferramentas disponíveis para qualquer cálculo."
)


class LimiteDePassos(Exception):
    """O agente não chegou a uma resposta dentro do limite de passos."""

def executar_agente(config: Config, pergunta: str) -> str:
    mensagens: list[dict] = [
        {"role": "system", "content": INSTRUCOES},
        {"role": "user", "content": pergunta},
    ]

    for _ in range(MAX_PASSOS):
        resposta = conversar(config, mensagens, DESCRICOES)
        mensagens.append(resposta)

        chamadas = resposta.get("tool_calls")
        if not chamadas:
            return resposta["content"]

        for chamada in chamadas:
            nome = chamada["function"]["name"]
            argumentos = chamada["function"]["arguments"]
            resultado = executar(nome, argumentos)
            print(f"  [ferramenta] {nome}({argumentos}) -> {resultado}")
            mensagens.append({"role": "tool", "tool_call_id": chamada["id"], "content": resultado})

    raise LimiteDePassos(f"sem resposta final após {MAX_PASSOS} passos")