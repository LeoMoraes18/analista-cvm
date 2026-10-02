from pathlib import Path

import psycopg

from analista.config import Config

ESQUEMA = Path(__file__).parent / "carga" / "schema.sql"


def conectar(config: Config) -> psycopg.Connection:
    return psycopg.connect(
        host=config.db_host,
        port=config.db_port,
        dbname=config.db_name,
        user=config.db_user,
        password=config.db_password,
        autocommit=True,
    )

def criar_esquema(conexao: psycopg.Connection) -> None:
    conexao.execute(ESQUEMA.read_text(encoding="utf-8"))