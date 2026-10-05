import json
import random
import re
import time
import urllib.error
import urllib.request

from analista.config import Config

TENTATIVAS = 4
STATUS_TRANSITORIOS = {429, 500, 502, 503, 504}
ESPERA_MAXIMA = 60


class ErroLLM(Exception):
    """Falha ao conversar com o modelo."""


def _recuo(tentativa: int) -> float:
    return 2**tentativa + random.random()


def _espera(erro: urllib.error.HTTPError, detalhe: str, tentativa: int) -> float:
    """Segundos até a próxima tentativa: o que o servidor pedir ou, sem pedido, o recuo."""
    cabecalho = erro.headers.get("Retry-After", "")
    pedido = re.search(r"(?:retry|try again) in ([0-9.]+)s", detalhe)
    try:
        if cabecalho:
            return float(cabecalho) + 1
        if pedido:
            return float(pedido.group(1)) + 1
    except ValueError:
        pass
    return _recuo(tentativa)


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
            "User-Agent": "analista-cvm/0.1",
        },
        method="POST",
    )

    for tentativa in range(TENTATIVAS):
        ultima = tentativa == TENTATIVAS - 1
        try:
            with urllib.request.urlopen(requisicao, timeout=60) as resposta:
                dados = json.load(resposta)
            return dados["choices"][0]["message"]
        except urllib.error.HTTPError as erro:
            detalhe = erro.read().decode("utf-8", errors="replace")
            if erro.code not in STATUS_TRANSITORIOS or ultima:
                raise ErroLLM(f"HTTP {erro.code}: {detalhe}") from erro
            espera = _espera(erro, detalhe, tentativa)
        except (urllib.error.URLError, TimeoutError) as erro:
            if ultima:
                raise ErroLLM(f"falha de rede: {erro}") from erro
            espera = _recuo(tentativa)
        time.sleep(min(espera, ESPERA_MAXIMA))

    raise ErroLLM("sem resposta após todas as tentativas")