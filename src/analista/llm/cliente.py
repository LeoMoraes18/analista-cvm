import json
import time
import urllib.error
import urllib.request
import random

from analista.config import Config


TENTATIVAS = 4
STATUS_TRANSITORIOS = {429, 500, 502, 503, 504}

class ErroLLM(Exception):
    """Falha ao conversar com o modelo."""

def conversar(config: Config, mensagens: list[dict], ferramentas: list[dict] | None = None) -> dict:
    """Envia a conversa inteira e devolve a mensagem de resposta do modelo."""
    corpo: dict = {"model": config.llm_modelo, "messages": mensagens}
    if ferramentas:
        corpo["tools"] = ferramentas

    requisicao = urllib.request.Request(
        config.llm_url + "/chat/completions",
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.llm_chave}",
        },
        method="POST"
    )

    for tentativa in range(TENTATIVAS):
        ultima = tentativa == TENTATIVAS - 1
        try:
            with urllib.request.urlopen(requisicao, timeout=60) as resposta:
                dados = json.load(resposta)
            break
        except urllib.error.HTTPError as erro:
            detalhe = erro.read().decode("utf-8", errors="replace")
            raise ErroLLM(f"HTTP {erro.code}: {detalhe}") from erro
        except (urllib.error.URLError, TimeoutError) as erro:
            if ultima:
                raise ErroLLM(f"falha de rede: {erro}") from erro

        time.sleep(2 ** tentativa + random.random())

    return dados["choices"][0]["message"]
