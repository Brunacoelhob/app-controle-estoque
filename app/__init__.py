"""Controle de Estoque (Flask). Use `create_app()` (application factory)."""

from __future__ import annotations

from flask import Flask

from .config import Config, ConfigTeste
from .extensions import criar_limiter, csrf, db, login_manager, migrate

CSP = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
)


def create_app(teste: bool = False, config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(ConfigTeste if teste else Config)
    if not teste:
        app.config.update(Config.carregar())
    if config:
        app.config.update(config)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter = criar_limiter()
    limiter.init_app(app)
    app.extensions["limitador"] = limiter  # referência forte: o Flask-Limiter só guarda uma referência fraca
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Faça login para continuar."
    login_manager.session_protection = "strong"  # invalida a sessão se IP/navegador mudarem

    from .models import Usuario

    @login_manager.user_loader
    def carregar_usuario(user_id: str):
        return db.session.get(Usuario, int(user_id)) if user_id.isdigit() else None

    from .cli import registrar_comandos
    from .routes import registrar_rotas

    registrar_rotas(app, limiter)
    registrar_comandos(app)

    @app.after_request
    def cabecalhos_de_seguranca(resposta):
        resposta.headers.setdefault("Content-Security-Policy", CSP)
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "same-origin")
        # Páginas autenticadas não devem ficar em cache do navegador/proxy.
        resposta.headers.setdefault("Cache-Control", "no-store")
        return resposta

    return app
