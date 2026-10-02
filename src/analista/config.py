import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    llm_url: str
    llm_chave: str
    llm_modelo: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str


def carregar_config() -> Config:
    return Config(
        llm_url=os.environ["LLM_URL"],
        llm_chave=os.environ.get("LLM_CHAVE", ""),
        llm_modelo=os.environ["LLM_MODELO"],
        db_host=os.environ["DB_HOST"],
        db_port=int(os.environ["DB_PORT"]),
        db_name=os.environ["DB_NAME"],
        db_user=os.environ["DB_USER"],
        db_password=os.environ["DB_PASSWORD"],
    )