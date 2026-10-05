import csv
import io
import urllib.error
import zipfile
from datetime import date
from pathlib import Path

import psycopg

from analista.carga.baixar import baixar
from analista.carga.fontes import (
    COLUNAS_CADASTRO,
    DELIMITADOR,
    ENCODING,
    URL_CADASTRO,
    URL_DFP,
    ARQUIVOS_DFP,
    COLUNAS_BRUTO,
)


PASTA_DADOS = Path("data")

SQL_BRUTO = """
    CREATE TEMP TABLE bruto (
        dt_refer TEXT, versao TEXT, cd_cvm TEXT, escala_moeda TEXT, ordem_exerc TEXT,
        dt_ini_exerc TEXT, dt_fim_exerc TEXT, cd_conta TEXT, ds_conta TEXT, vl_conta TEXT
    ) ON COMMIT DROP
"""

SQL_TRANSFORMAR = """
    WITH ultima AS (
        SELECT cd_cvm, dt_refer, max(versao::integer) AS versao
        FROM bruto
        GROUP BY cd_cvm, dt_refer
    ),
    filtrado AS (
        SELECT DISTINCT b.cd_cvm::integer AS cd_cvm, b.dt_refer::date AS dt_refer,
               b.versao::integer AS versao, b.dt_ini_exerc::date AS dt_ini_exerc,
               b.dt_fim_exerc::date AS dt_fim_exerc, b.cd_conta, b.ds_conta,
               b.vl_conta::numeric
                   * CASE b.escala_moeda WHEN 'MIL' THEN 1000 ELSE 1 END AS vl_conta
        FROM bruto b
        JOIN ultima u ON u.cd_cvm = b.cd_cvm AND u.dt_refer = b.dt_refer
                     AND u.versao = b.versao::integer
        WHERE b.ordem_exerc = 'ÚLTIMO'
          AND NOT starts_with(b.cd_conta, '3.99')
    ),
    ambiguo AS (
        SELECT DISTINCT cd_cvm, dt_fim_exerc
        FROM filtrado
        GROUP BY cd_cvm, dt_fim_exerc, cd_conta
        HAVING count(*) > 1
    ),
    registrado AS (
        INSERT INTO inconsistencia (cd_cvm, demonstracao, consolidado, dt_fim_exerc, motivo)
        SELECT cd_cvm, %(demonstracao)s::text, %(consolidado)s::boolean, dt_fim_exerc,
               'conta repetida com conteúdo diferente no mesmo documento'
        FROM ambiguo
    )
    INSERT INTO conta (cd_cvm, demonstracao, consolidado, dt_refer, versao,
                       dt_ini_exerc, dt_fim_exerc, cd_conta, ds_conta, vl_conta)
    SELECT f.cd_cvm, %(demonstracao)s::text, %(consolidado)s::boolean, f.dt_refer, f.versao,
           f.dt_ini_exerc, f.dt_fim_exerc, f.cd_conta, f.ds_conta, f.vl_conta
    FROM filtrado f
    WHERE NOT EXISTS (
        SELECT 1 FROM ambiguo a
        WHERE a.cd_cvm = f.cd_cvm AND a.dt_fim_exerc = f.dt_fim_exerc
    )
"""


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

    ano_atual = date.today().year
    for ano in range(ano_atual - 5, ano_atual):
        if ja_carregado(conexao, f"dfp_cia_aberta_{ano}.zip"):
            continue
        total = carregar_dfp(conexao, ano)
        if total is None:
            print(f"DFP {ano}: arquivo não disponível")
        else:
            print(f"DFP {ano}: {total} contas carregadas")

def carregar_dfp(conexao: psycopg.Connection, ano: int) -> int | None:
    """Carrega as demonstrações de um ano. Devolve None se o arquivo não existir na CVM."""
    try:
        caminho = baixar(URL_DFP.format(ano=ano), PASTA_DADOS)
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            return None
        raise
    total = 0
    try:
        with conexao.transaction(), zipfile.ZipFile(caminho) as zf:
            conexao.execute(SQL_BRUTO)
            for (demonstracao, consolidado), trecho in ARQUIVOS_DFP.items():
                conexao.execute("TRUNCATE bruto")
                membro = f"dfp_cia_aberta_{trecho}_{ano}.csv"
                with (
                    zf.open(membro) as binario,
                    conexao.cursor().copy("COPY bruto FROM STDIN") as copia,
                ):
                    texto = io.TextIOWrapper(binario, encoding=ENCODING, newline="")
                    leitor = csv.DictReader(texto, delimiter=DELIMITADOR, quoting=csv.QUOTE_NONE)
                    for registro in leitor:
                        copia.write_row([registro.get(c) or None for c in COLUNAS_BRUTO])
                parametros = {"demonstracao": demonstracao, "consolidado": consolidado}
                total += conexao.execute(SQL_TRANSFORMAR, parametros).rowcount
            conexao.execute(
                "INSERT INTO carga (arquivo, linhas) VALUES (%s, %s)", (caminho.name, total)
            )
    finally:
        caminho.unlink()
    return total