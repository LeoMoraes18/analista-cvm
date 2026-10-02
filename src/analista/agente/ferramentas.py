import json


def variacao_percentual(valor_inicial: float, valor_final: float) -> float:
    return round((valor_final - valor_inicial) / valor_inicial * 100, 2)

def margem(lucro: float, receita: float) -> float:
    return round(lucro / receita * 100, 2)

FUNCOES = {
    "variacao_percentual": variacao_percentual,
    "margem": margem,
}

DESCRICOES = [
        {
            "type": "function",
            "function": {
                "name": "variacao_percentual",
                "description": "Calcula a variação percentual entre dois valores, por exemplo o crescimento da receita de um ano para o outro.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "valor_inicial": {"type": "number", "description": "Valor do período mais antigo"},
                        "valor_final": {"type": "number", "description": "Valor do período mais recente"},
                    },
                    "required": ["valor_inicial", "valor_final"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "margem",
                "description": "Calcula uma margem em percentual: quanto o lucro representa da receita.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lucro": {"type": "number", "description": "Lucro do período"},
                        "receita": {"type": "number", "description": "Receita do mesmo período"},
                    },
                    "required": ["lucro", "receita"]
                },
            }
        }
    ]

def executar(nome: str, argumentos_json: str) -> str:
    """Executa uma ferramenta e devolve o resultado como texto JSON, inclusive em caso de erro."""
    if nome not in FUNCOES:
        return json.dumps({"erro": f"ferramenta inexistente: {nome}"})
    try:
        argumentos = json.loads(argumentos_json)
        resultado = FUNCOES[nome](**argumentos)
    except Exception as erro:
        return json.dumps({"erro": f"{type(erro).__name__}: {erro}"})

    return json.dumps({"resultado": resultado})
