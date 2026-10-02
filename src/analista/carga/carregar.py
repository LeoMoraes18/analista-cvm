import csv
from pathlib import Path

import psycopg

from analista.carga.baixar import baixar
from analista.carga.fontes import COLUNAS_CADASTRO, DELIMITADOR, ENCODING, URL_CADASTRO

PASTA_DADOS = Path("data")


def ja_carregado(conexao: psycopg.Connection, arquivo: str) -> bool:
    consulta = "SELECT 1 FROM carga WHERE arquivo = %s"
    return conexao.execute(consulta, (arquivo,)).fetchone() is not None

def carregar_cadastro(conexao: psycopg.Connection) -> int:
    caminho = baixar(URL_CADASTRO, PASTA_DADOS)
    colunas = ", ".join(COLUNAS_CADASTRO.values())
    linhas = 0
    try:
        with conexao.transaction():
            conexao.execute("TRUNCATE empresa")
            with (
                open(caminho, encoding=ENCODING, newline="") as f,
                conexao.cursor().copy(f"COPY empresa ({colunas}) FROM STDIN") as copia,
            ):
                leitor = csv.DictReader(f, delimiter=DELIMITADOR, quoting=csv.QUOTE_NONE)
                vistos: dict[str, list] = {}
                for registro in leitor:
                    linha = [registro[c] or None for c in COLUNAS_CADASTRO]
                    codigo = registro["CD_CVM"]
                    if codigo in vistos:
                        if vistos[codigo] != linha:
                            raise ValueError(f"CD_CVM {codigo} repetido com dados diferentes")
                        continue
                    vistos[codigo] = linha
                    copia.write_row(linha)
                    linhas += 1
            conexao.execute(
                "INSERT INTO carga (arquivo, linhas) VALUES (%s, %s)", (caminho.name, linhas)
            )
    finally:
        caminho.unlink()
    return linhas

def garantir_carga(conexao: psycopg.Connection) -> None:
    """Carrega o que ainda não está no banco. Rodar de novo não repete nada."""
    if not ja_carregado(conexao, "cad_cia_aberta.csv"):
        total = carregar_cadastro(conexao)
        print(f"cadastro carregado: {total} empresas")