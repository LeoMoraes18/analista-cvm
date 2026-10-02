import json
from functools import partial

import psycopg
from psycopg.rows import dict_row


def variacao_percentual(valor_inicial: float, valor_final: float) -> float:
    return round((valor_final - valor_inicial) / valor_inicial * 100, 2)

def margem(lucro: float, receita: float) -> float:
    return round(lucro / receita * 100, 2)

def buscar_empresa(conexao: psycopg.Connection, nome: str) -> list[dict]:
    consulta = """
        SELECT cd_cvm, denom_social, denom_comerc, setor_ativ, situacao
        FROM empresa
        WHERE unaccent(denom_social) ILIKE unaccent(%(padrao)s)
           OR unaccent(denom_comerc) ILIKE unaccent(%(padrao)s)
        ORDER BY (situacao = 'ATIVO') DESC, denom_social
        LIMIT 11
    """
    with conexao.cursor(row_factory=dict_row) as cursor:
        linhas = cursor.execute(consulta, {"padrao": f"%{nome}%"}).fetchall()
    return {"empresas": linhas[:10], "ha_mais_resultados": len(linhas) > 10}

def montar_funcoes(conexao: psycopg.Connection) -> dict:
    return {
        "variacao_percentual": variacao_percentual,
        "margem": margem,
        "buscar_empresa": partial(buscar_empresa, conexao),
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
            },
        },
        {
            "type": "function",
            "function": {
                "name": "buscar_empresa",
                "description": "Busca companhias abertas no cadastro da CVM por parte do nome. Devolve até 10 resultados com código CVM, razão social, nome comercial, setor e situação.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string", "description": "Parte do nome da empresa, por exemplo 'petrobras'"},
                    },
                    "required": ["nome"],
                },
            },
        },
    ]

def executar(funcoes: dict, nome: str, argumentos_json: str) -> str:
    """Executa uma ferramenta e devolve o resultado como texto JSON, inclusive em caso de erro."""
    if nome not in funcoes:
        return json.dumps({"erro": f"ferramenta inexistente: {nome}"})
    try:
        argumentos = json.loads(argumentos_json)
        resultado = funcoes[nome](**argumentos)
    except Exception as erro:
        return json.dumps({"erro": f"{type(erro).__name__}: {erro}"})

    return json.dumps({"resultado": resultado}, ensure_ascii=False)
