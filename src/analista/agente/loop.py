import psycopg

from analista.agente.ferramentas import DESCRICOES, executar, montar_funcoes
from analista.config import Config
from analista.llm.cliente import conversar

MAX_PASSOS = 8

INSTRUCOES = """\
Você é um analista de demonstrações financeiras de companhias abertas brasileiras.
Responda em português, em texto simples, sem fórmulas em LaTeX.

Fonte dos dados
- Tudo o que você sabe sobre empresas vem das ferramentas: o cadastro da CVM e a
  demonstração de resultado (DRE) anual dos últimos cinco exercícios.
- Nunca cite nomes, códigos ou valores de memória. Se as ferramentas não trouxerem
  o dado, diga que ele não está disponível.

Empresas
- Comece por buscar_empresa para descobrir o código CVM.
- Se a busca devolver mais de uma empresa que possa ser a pedida, diga qual você
  usou, com nome e código, e cite as outras.
- Se a busca não devolver nada, diga que não encontrou.

Valores
- Use o nome da empresa e a descrição das contas exatamente como vieram das ferramentas.
- Se uma ferramenta devolver um aviso, inclua-o na resposta.
- Escreva valores com a unidade por extenso, por exemplo "R$ 490,8 bilhões".

Cálculos
- Você não sabe fazer contas. Todo percentual, razão ou diferença deve sair de uma
  ferramenta de cálculo, mesmo quando parecer simples.
"""


class LimiteDePassos(Exception):
    """O agente não chegou a uma resposta dentro do limite de passos."""

def executar_agente(config: Config, conexao: psycopg.Connection, pergunta: str) -> str:
    mensagens: list[dict] = [
        {"role": "system", "content": INSTRUCOES},
        {"role": "user", "content": pergunta},
    ]

    funcoes = montar_funcoes(conexao)

    for _ in range(MAX_PASSOS):
        resposta = conversar(config, mensagens, DESCRICOES)
        mensagens.append(resposta)
        chamadas = resposta.get("tool_calls")

        if not chamadas:
            return resposta["content"]

        for chamada in chamadas:
            nome = chamada["function"]["name"]
            argumentos = chamada["function"]["arguments"]
            resultado = executar(funcoes, nome, argumentos)
            print(f"  [ferramenta] {nome}({argumentos}) -> {resultado}")
            mensagens.append({"role": "tool", "tool_call_id": chamada["id"], "content": resultado})

    raise LimiteDePassos(f"sem resposta final após {MAX_PASSOS} passos")