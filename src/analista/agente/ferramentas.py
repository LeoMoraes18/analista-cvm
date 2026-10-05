import json
from functools import partial

import psycopg
from psycopg.rows import dict_row


SQL_CONTAS = """
    WITH escolhido AS (
        SELECT consolidado, dt_fim_exerc
        FROM conta
        WHERE cd_cvm = %(cd_cvm)s AND demonstracao = 'DRE'
          AND EXTRACT(YEAR FROM dt_fim_exerc) = %(ano)s
        ORDER BY consolidado DESC, dt_fim_exerc DESC
        LIMIT 1
    )
    SELECT c.consolidado, c.dt_ini_exerc, c.dt_fim_exerc, c.cd_conta, c.ds_conta, c.vl_conta
    FROM conta c
    JOIN escolhido e USING (consolidado, dt_fim_exerc)
    WHERE c.cd_cvm = %(cd_cvm)s AND c.demonstracao = 'DRE'
      AND c.cd_conta ~ '^3[.][0-9]{2}$'
    ORDER BY c.cd_conta
"""

SQL_INCONSISTENTE = """
    SELECT consolidado
    FROM inconsistencia
    WHERE cd_cvm = %(cd_cvm)s AND demonstracao = 'DRE'
      AND EXTRACT(YEAR FROM dt_fim_exerc) = %(ano)s
"""

SQL_ANOS = """
    SELECT DISTINCT EXTRACT(YEAR FROM dt_fim_exerc)::integer
    FROM conta
    WHERE cd_cvm = %(cd_cvm)s AND demonstracao = 'DRE'
    ORDER BY 1
"""

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

def obter_contas(conexao: psycopg.Connection, cd_cvm: int, ano: int) -> dict:
    """Linhas principais da DRE anual de uma empresa, em reais."""
    parametros = {"cd_cvm": int(cd_cvm), "ano": int(ano)}
    linhas = conexao.execute(SQL_CONTAS, parametros).fetchall()
    rejeitados = [r[0] for r in conexao.execute(SQL_INCONSISTENTE, parametros)]

    if not linhas:
        if rejeitados:
            raise ValueError(
                f"A DRE de {ano} dessa empresa está inconsistente no arquivo da CVM "
                "e não foi carregada. Informe isso ao usuário; não estime valores."
            )
        anos = [r[0] for r in conexao.execute(SQL_ANOS, parametros)]
        if anos:
            raise ValueError(f"Não há DRE de {ano} para essa empresa. Anos disponíveis: {anos}.")
        raise ValueError(
            "Não há DRE carregada para esse código CVM. Confirme o código com buscar_empresa."
        )

    consolidado, inicio, fim = linhas[0][:3]

    empresa = conexao.execute(
        "SELECT denom_social FROM empresa WHERE cd_cvm = %s", (parametros["cd_cvm"],)
    ).fetchone()

    resultado = {
        "empresa": empresa[0] if empresa else None,
        "cd_cvm": parametros["cd_cvm"],
        "consolidado": consolidado,
        "periodo": {"inicio": inicio.isoformat() if inicio else None, "fim": fim.isoformat()},
        "moeda": "reais",
        "contas": [
            {
                "codigo": codigo,
                "descricao": descricao,
                "valor": float(valor) if valor is not None else None,
            }
            for _, _, _, codigo, descricao, valor in linhas
        ],
    }
    if not consolidado and True in rejeitados:
        resultado["aviso"] = (
            "A DRE consolidada desse ano está inconsistente na CVM; "
            "estes valores são da demonstração individual (só a controladora)."
        )
    return resultado

def montar_funcoes(conexao: psycopg.Connection) -> dict:
    return {
        "variacao_percentual": variacao_percentual,
        "margem": margem,
        "buscar_empresa": partial(buscar_empresa, conexao),
        "obter_contas": partial(obter_contas, conexao),
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
        {
            "type": "function",
            "function": {
                "name": "obter_contas",
                "description": (
                    "Devolve as linhas principais da demonstração de resultado (DRE) anual de uma "
                    "empresa, em reais: receita, custos, resultado bruto, lucro ou prejuízo do "
                    "período. Use buscar_empresa antes para descobrir o cd_cvm. Escolha a linha "
                    "pela descrição da conta, pois os códigos variam entre bancos, seguradoras e "
                    "demais empresas."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cd_cvm": {"type": "integer", "description": "Código CVM da empresa."},
                        "ano": {"type": "integer", "description": "Ano do exercício, por exemplo 2024."},
                    },
                    "required": ["cd_cvm", "ano"],
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
