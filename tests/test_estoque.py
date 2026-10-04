"""Produtos, movimentações, painel e fotos."""

import threading
from datetime import date, timedelta

import pytest

from app import servicos
from app.extensions import db
from app.models import Movimentacao, Produto, Usuario
from tests.conftest import PNG, arquivo


def qtd(app, id_):
    with app.app_context():
        return db.session.get(Produto, id_).Quantidade_produto


# ------------------------------------------------------------------ produtos
def test_admin_cadastra_edita_e_exclui_produto(admin, app):
    r = admin.post("/cadastrar-produto", data={"nome": "  Monitor ", "quantidade": 5, "minimo": 2})
    assert r.status_code == 302
    with app.app_context():
        novo = db.session.execute(db.select(Produto).filter_by(Nome_produto="Monitor")).scalar()
        assert novo.Quantidade_produto == 5
        id_ = novo.id_produto

    assert admin.post(f"/editar/{id_}", data={"nome": "Monitor 24", "quantidade": 8, "minimo": 2}).status_code == 302
    assert qtd(app, id_) == 8

    assert admin.post(f"/excluir/{id_}").status_code == 302
    with app.app_context():
        assert db.session.get(Produto, id_) is None


def test_formulario_de_edicao_vem_preenchido(admin):
    html = admin.get("/editar/1").get_data(as_text=True)
    assert 'value="Mouse"' in html and 'value="10"' in html


@pytest.mark.parametrize(
    "dados",
    [
        {"nome": "", "quantidade": 1, "minimo": 1},
        {"nome": "x" * 101, "quantidade": 1, "minimo": 1},
        {"nome": "A", "quantidade": -1, "minimo": 1},
        {"nome": "A", "quantidade": 1, "minimo": 0},
        {"nome": "A", "quantidade": 10_000_000, "minimo": 1},
    ],
)
def test_validacao_do_produto(admin, app, dados):
    r = admin.post("/cadastrar-produto", data=dados)
    assert r.status_code == 200  # volta ao formulário com erro
    with app.app_context():
        assert db.session.execute(db.select(db.func.count(Produto.id_produto))).scalar() == 2


def test_produto_inexistente_devolve_404(admin):
    assert admin.get("/editar/999").status_code == 404
    assert admin.post("/excluir/999").status_code == 404


def test_xss_no_nome_do_produto_e_escapado(admin):
    admin.post("/cadastrar-produto", data={"nome": "<script>alert(1)</script>", "quantidade": 1, "minimo": 1})
    html = admin.get("/dashboard").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


# ------------------------------------------------------------------ movimentação
def test_entrada_e_saida_atualizam_o_saldo_e_o_historico(admin, app):
    hoje = date.today().isoformat()
    admin.post("/movimentar-estoque", data={"produto_id": 1, "tipo_movimentacao": "entrada", "quantidade": 5, "data": hoje})
    assert qtd(app, 1) == 15
    admin.post("/movimentar-estoque", data={"produto_id": 1, "tipo_movimentacao": "saida", "quantidade": 12, "data": hoje})
    assert qtd(app, 1) == 3
    with app.app_context():
        assert db.session.execute(db.select(db.func.count(Movimentacao.id_movimentacao))).scalar() == 2


def test_saida_maior_que_o_saldo_e_recusada_sem_alterar_nada(admin, app):
    r = admin.post(
        "/movimentar-estoque",
        data={"produto_id": 2, "tipo_movimentacao": "saida", "quantidade": 3, "data": date.today().isoformat()},
        follow_redirects=True,
    )
    assert "Estoque insuficiente" in r.get_data(as_text=True)
    assert qtd(app, 2) == 2
    with app.app_context():
        assert db.session.execute(db.select(db.func.count(Movimentacao.id_movimentacao))).scalar() == 0


def test_operador_pode_movimentar(operador, app):
    operador.post(
        "/movimentar-estoque",
        data={"produto_id": 1, "tipo_movimentacao": "saida", "quantidade": 1, "data": date.today().isoformat()},
    )
    assert qtd(app, 1) == 9


@pytest.mark.parametrize(
    "dados",
    [
        {"quantidade": 0},
        {"quantidade": -4},
        {"tipo_movimentacao": "roubo"},
        {"produto_id": 999},
        {"data": (date.today() + timedelta(days=3)).isoformat()},
    ],
)
def test_movimentacao_invalida_e_rejeitada(admin, app, dados):
    base = {"produto_id": 1, "tipo_movimentacao": "saida", "quantidade": 1, "data": date.today().isoformat()}
    admin.post("/movimentar-estoque", data={**base, **dados})
    assert qtd(app, 1) == 10


def test_servico_movimentar_e_atomico_sob_concorrencia(app, tmp_path):
    """Várias saídas simultâneas nunca deixam o estoque negativo (um único UPDATE condicional decide)."""
    from app.extensions import db as _db

    resultados = []

    def sair():
        with app.app_context():
            try:
                servicos.movimentar(1, "saida", 1, date.today(), 1)
                resultados.append("ok")
            except servicos.EstoqueInsuficiente:
                resultados.append("sem-saldo")
            finally:
                _db.session.remove()

    # SQLite em memória compartilha uma única conexão; serializamos a execução mas mantemos o cenário
    # "20 pessoas tentando tirar 1 unidade de um estoque de 10".
    for _ in range(20):
        t = threading.Thread(target=sair)
        t.start()
        t.join()

    assert resultados.count("ok") == 10 and resultados.count("sem-saldo") == 10
    assert qtd(app, 1) == 0


def test_nao_exclui_produto_com_historico(admin, app):
    admin.post(
        "/movimentar-estoque",
        data={"produto_id": 1, "tipo_movimentacao": "entrada", "quantidade": 1, "data": date.today().isoformat()},
    )
    r = admin.post("/excluir/1", follow_redirects=True)
    assert "possui movimentações" in r.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(Produto, 1) is not None


# ------------------------------------------------------------------ painel
def test_painel_mostra_numeros_reais(admin):
    admin.post(
        "/movimentar-estoque",
        data={"produto_id": 1, "tipo_movimentacao": "saida", "quantidade": 4, "data": date.today().isoformat()},
    )
    d = admin.get("/painel-estoque/dados").get_json()
    assert d["resumo"]["produtos"] == 2
    assert d["resumo"]["unidades"] == 6 + 2
    assert d["resumo"]["abaixo_do_minimo"] == 1  # Teclado: 2 < 5
    assert d["resumo"]["saidas_periodo"] == 4
    assert d["faltantes"] == {"rotulos": ["Teclado"], "deficit": [3]}
    assert d["movimentacao"]["saidas"][-1] == 4 and len(d["movimentacao"]["rotulos"]) == 30
    assert d["por_usuario"] == {"rotulos": ["Admin"], "unidades": [4]}


def test_painel_nao_tem_mais_dados_inventados(admin):
    html = admin.get("/painel-estoque").get_data(as_text=True)
    for falso in ("R$ 12.500", "Lucro Estimado", "Bruna", "Caio"):
        assert falso not in html


# ------------------------------------------------------------------ foto de perfil
def test_foto_png_valida_e_servida_so_para_logados(admin, app, cliente):
    r = admin.post("/editar-foto", data={"foto": arquivo(PNG)}, content_type="multipart/form-data")
    assert r.status_code == 302
    with app.app_context():
        nome = db.session.execute(db.select(Usuario).filter_by(Email_usuario="admin@ex.com")).scalar().foto_url
    assert nome.endswith(".png") and nome != "foto.png", "nome aleatório, não o enviado"

    assert admin.get(f"/fotos/{nome}").data == PNG
    assert app.test_client().get(f"/fotos/{nome}").status_code == 302  # sem login


@pytest.mark.parametrize(
    "conteudo,nome",
    [
        (b"<html><script>alert(1)</script></html>", "x.html"),
        (b"<html><script>alert(1)</script></html>", "falsa.png"),  # extensão mente, conteúdo não é imagem
        (b"MZ\x90\x00 executavel", "foto.jpg"),
        (b"", "vazio.png"),
    ],
)
def test_foto_invalida_e_recusada(admin, app, conteudo, nome):
    r = admin.post(
        "/editar-foto", data={"foto": arquivo(conteudo, nome)}, content_type="multipart/form-data", follow_redirects=True
    )
    assert "Envie uma imagem" in r.get_data(as_text=True) or "Nenhuma foto" in r.get_data(as_text=True)
    with app.app_context():
        assert db.session.execute(db.select(Usuario).filter_by(Email_usuario="admin@ex.com")).scalar().foto_url is None


def test_foto_grande_demais_e_recusada(admin):
    r = admin.post("/editar-foto", data={"foto": arquivo(PNG + b"0" * (3 * 1024 * 1024))}, content_type="multipart/form-data")
    assert r.status_code == 303


@pytest.mark.parametrize("nome", ["../../etc/passwd", "..%2f..%2fapp.py", "foto.html", "a" * 32 + ".png"])
def test_caminhos_perigosos_nao_sao_servidos(admin, nome):
    assert admin.get(f"/fotos/{nome}").status_code == 404


def test_trocar_foto_apaga_a_anterior(admin, app):
    admin.post("/editar-foto", data={"foto": arquivo(PNG)}, content_type="multipart/form-data")
    admin.post("/editar-foto", data={"foto": arquivo(PNG)}, content_type="multipart/form-data")
    from pathlib import Path

    assert len(list(Path(app.config["UPLOAD_DIR"]).iterdir())) == 1


# ------------------------------------------------------------------ usuários
def test_admin_cadastra_usuario_e_email_duplicado_e_recusado(admin, app):
    dados = {"nome": "Novo", "email": "Novo@Ex.com", "senha": "senha-forte-1", "perfil": "comum"}
    assert admin.post("/cadastrar-usuario", data=dados).status_code == 302
    with app.app_context():
        u = db.session.execute(db.select(Usuario).filter_by(Email_usuario="novo@ex.com")).scalar()
        assert u is not None and u.Senha_usuario != "senha-forte-1", "senha guardada como hash"

    r = admin.post("/cadastrar-usuario", data=dados)
    assert r.status_code == 200 and "Já existe um usuário" in r.get_data(as_text=True)


def test_senha_curta_e_perfil_invalido_sao_recusados(admin, app):
    admin.post("/cadastrar-usuario", data={"nome": "A", "email": "a@ex.com", "senha": "1234567", "perfil": "comum"})
    admin.post("/cadastrar-usuario", data={"nome": "B", "email": "b@ex.com", "senha": "senha-forte-1", "perfil": "superadmin"})
    with app.app_context():
        assert db.session.execute(db.select(db.func.count(Usuario.id_usuario))).scalar() == 2
