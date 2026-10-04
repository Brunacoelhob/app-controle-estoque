from app.extensions import db
from app.models import Usuario


def test_criar_admin_pede_senha_e_grava_hash(app):
    runner = app.test_cli_runner()
    r = runner.invoke(
        args=["criar-admin", "--nome", "Chefe", "--email", "Chefe@Ex.com"], input="senha-bem-forte\nsenha-bem-forte\n"
    )
    assert r.exit_code == 0, r.output
    with app.app_context():
        u = db.session.execute(db.select(Usuario).filter_by(Email_usuario="chefe@ex.com")).scalar()
        assert u.is_admin and u.Senha_usuario != "senha-bem-forte"


def test_criar_admin_recusa_senha_curta_e_email_repetido(app):
    runner = app.test_cli_runner()
    curta = runner.invoke(args=["criar-admin", "--nome", "X", "--email", "x@ex.com"], input="1234\n1234\n")
    assert curta.exit_code != 0 and "pelo menos 8" in curta.output

    repetido = runner.invoke(
        args=["criar-admin", "--nome", "X", "--email", "admin@ex.com"], input="senha-bem-forte\nsenha-bem-forte\n"
    )
    assert repetido.exit_code != 0 and "Já existe" in repetido.output


def test_listar_usuarios_nao_mostra_hash(app):
    r = app.test_cli_runner().invoke(args=["listar-usuarios"])
    assert "admin@ex.com" in r.output
    assert "pbkdf2" not in r.output and "scrypt" not in r.output
