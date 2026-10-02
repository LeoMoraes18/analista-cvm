import shutil
import urllib.request
from pathlib import Path


def baixar(url: str, pasta: Path) -> Path:
    """Baixa o arquivo para a pasta e devolve o caminho."""
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / url.rsplit("/", 1)[-1]
    with urllib.request.urlopen(url, timeout=120) as resposta, open(destino, "wb") as arquivo:
        shutil.copyfileobj(resposta, arquivo)
    return destino