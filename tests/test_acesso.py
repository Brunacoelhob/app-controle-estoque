"""Autenticação, autorização e proteções web."""

import pytest

from app import create_app
from app.config import ConfiguracaoInvalida
from app.extensions import db
from app.models import Produto
from tests.conftest import SENHA, entrar

ROTAS_PROTEGIDAS = [
    "/dashboard",
    "/cadastrar-produto",
    "/editar/1",
    "/cadastrar-usuario",
    "/movimentar-estoque",
    "/painel-estoque",
]


@pytest.mark.parametrize("rota", ROTAS_PROTEGIDAS)
def test_rotas_exigem_login(cliente, rota):
    r = cliente.get(rota)
    assert r.status_code == 302 and "/" in r.headers["Location"]


def test_login_correto_e_senha_errada(cliente):
    assert entrar(cliente, "admin@ex.com", SENHA).headers["Location"].endswith("/dashboard")
    sair = cliente.post("/logout")
    assert sair.status_code == 302

    r = entrar(cliente, "admin@ex.com", "errada-errada")
    assert r.status_code == 200 and "inválidos" in r.get_data(as_text=True)


def test_email_inexistente_tem_a_mesma_resposta_que_senha_errada(cliente):
    a = entrar(cliente, "ninguem@ex.com", "qualquer-coisa")
    b = entrar(cliente, "admin@ex.com", "qualquer-coisa")
    assert a.status_code == b.status_code == 200
    assert "Email ou senha inválidos." in a.get_data(as_text=True)
    assert "Email ou senha inválidos." in b.get_data(as_text=True)


def test_email_do_login_ignora_maiusculas(cliente):
    assert entrar(cliente, "ADMIN@EX.COM", SENHA).status_code == 302


def test_logout_so_por_post(admin):
    assert admin.get("/logout").status_code == 405
    assert admin.post("/logout").status_code == 302
    assert admin.get("/dashboard").status_code == 302


def test_excluir_nao_funciona_por_get(admin, app):
    # Antes: GET /excluir/<id> apagava o produto, então um <img src="/excluir/1"> em outro site bastava (CSRF).
    assert admin.get("/excluir/1").status_code == 405
    with app.app_context():
        assert db.session.get(Produto, 1) is not None


def test_operador_nao_altera_produtos_nem_usuarios(operador, app):
    for rota in ("/cadastrar-produto", "/editar/1", "/cadastrar-usuario"):
        assert operador.get(rota).status_code == 303, rota
    r = operador.post("/excluir/1")
    assert r.status_code == 303
    with app.app_context():
        assert db.session.get(Produto, 1) is not None, "operador não conseguiu apagar"


def test_operador_nao_ve_botoes_de_administrador(operador, admin):
    html_op = operador.get("/dashboard").get_data(as_text=True)
    html_admin = admin.get("/dashboard").get_data(as_text=True)
    assert "Cadastrar Produto" not in html_op and "Cadastrar Usuário" not in html_op
    assert "Excluir" not in html_op
    assert "Cadastrar Produto" in html_admin and "Excluir" in html_admin


def test_csrf_bloqueia_post_sem_token(app):
    app.config["WTF_CSRF_ENABLED"] = True
    c = app.test_client()
    r = c.post("/", data={"email": "admin@ex.com", "senha": SENHA})
    assert r.status_code == 400  # token ausente


def test_cabecalhos_de_seguranca(cliente):
    h = cliente.get("/").headers
    assert "default-src 'self'" in h["Content-Security-Policy"]
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert h["Cache-Control"] == "no-store"


def test_nao_ha_script_inline_nas_paginas(admin):
    # A CSP bloqueia scripts inline; garantimos que nenhuma página depende deles.
    for rota in ("/dashboard", "/painel-estoque", "/movimentar-estoque", "/cadastrar-produto"):
        html = admin.get(rota).get_data(as_text=True)
        assert "onclick=" not in html and "onchange=" not in html, rota
        for trecho in html.split("<script")[1:]:
            tag = trecho.split(">", 1)[0]
            assert "src=" in tag or "application/json" in tag, f"script inline em {rota}"


def test_limite_de_tentativas_de_login(fabrica_app):
    app = fabrica_app(RATELIMIT_ENABLED=True, LIMITE_LOGIN="3 per minute")
    c = app.test_client()
    codigos = [entrar(c, "admin@ex.com", "errada-errada").status_code for _ in range(5)]
    assert codigos[:3] == [200, 200, 200]
    assert codigos[3] == 429 and codigos[4] == 429


def test_secret_key_e_obrigatoria_fora_dos_testes(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ConfiguracaoInvalida, match="SECRET_KEY"):
        create_app()
    monkeypatch.setenv("SECRET_KEY", "curta")
    with pytest.raises(ConfiguracaoInvalida):
        create_app()


def test_saude(cliente):
    r = cliente.get("/saude")
    assert r.status_code == 200 and r.get_json() == {"status": "ok"}
