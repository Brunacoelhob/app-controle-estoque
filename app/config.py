"""Configuração por ambiente. Nenhum segredo fica no código."""

from __future__ import annotations

import os
from pathlib import Path


class ConfiguracaoInvalida(RuntimeError):
    """Falta alguma variável obrigatória; a mensagem diz qual."""


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB: limita o tamanho de qualquer requisição (inclui upload)

    # Cookies de sessão: não acessíveis por JavaScript e não enviados em requisições cruzadas.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"  # ligue em produção (HTTPS)

    LIMITE_LOGIN = os.environ.get("LIMITE_LOGIN", "10 per minute")
    RATELIMIT_STORAGE_URI = "memory://"

    @classmethod
    def carregar(cls) -> dict:
        """Lê o ambiente. SECRET_KEY é obrigatória: sem ela as sessões poderiam ser forjadas."""
        chave = os.environ.get("SECRET_KEY", "").strip()
        if len(chave) < 16:
            raise ConfiguracaoInvalida(
                "Defina SECRET_KEY (mínimo 16 caracteres) no ambiente ou no .env. "
                'Gere uma com: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        return {
            "SECRET_KEY": chave,
            "SQLALCHEMY_DATABASE_URI": os.environ.get("DATABASE_URL", "sqlite:///estoque.db"),
            "UPLOAD_DIR": os.environ.get("UPLOAD_DIR", ""),  # vazio = <instance>/uploads
        }


class ConfigTeste(Config):
    TESTING = True
    SECRET_KEY = "chave-so-para-testes-nao-usar"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    UPLOAD_DIR = ""


def pasta_de_uploads(app) -> Path:
    destino = app.config.get("UPLOAD_DIR") or str(Path(app.instance_path) / "uploads")
    caminho = Path(destino)
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho
