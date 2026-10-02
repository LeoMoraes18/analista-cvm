import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    llm_url: str
    llm_chave: str
    llm_modelo: str


def carregar_config() -> Config:
    return Config(
        llm_url=os.environ["LLM_URL"],
        llm_chave=os.environ.get("LLM_CHAVE", ""),
        llm_modelo=os.environ["LLM_MODELO"],
    )