import io

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Produto, Usuario

SENHA = "senha-segura-1"

# PNG mínimo válido (1x1 pixel): o servidor valida pelo conteúdo, não pela extensão.
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture()
def fabrica_app(tmp_path):
    """Cria apps de teste com configurações opcionais (ex.: ligar o limitador de tentativas)."""
    criados = []

    def criar(**config):
        app = create_app(teste=True, config={"UPLOAD_DIR": str(tmp_path / "uploads"), **config})
        with app.app_context():
            db.create_all()
            db.session.add_all(
                [
                    Usuario(
                        Nome_usuario="Admin",
                        Email_usuario="admin@ex.com",
                        Senha_usuario=generate_password_hash(SENHA),
                        Perfil_usuario="admin",
                    ),
                    Usuario(
                        Nome_usuario="Operador",
                        Email_usuario="op@ex.com",
                        Senha_usuario=generate_password_hash(SENHA),
                        Perfil_usuario="comum",
                    ),
                    Produto(Nome_produto="Mouse", Quantidade_produto=10, Minimo_produto=3),
                    Produto(Nome_produto="Teclado", Quantidade_produto=2, Minimo_produto=5),
                ]
            )
            db.session.commit()
        # O contexto NÃO fica aberto durante o teste: senão o `g` (e o usuário logado em cache) vazaria entre requisições.
        criados.append(app)
        return app

    yield criar
    for app in criados:
        with app.app_context():
            db.session.remove()
            db.drop_all()


@pytest.fixture()
def app(fabrica_app):
    return fabrica_app()


@pytest.fixture()
def cliente(app):
    return app.test_client()


def entrar(cliente, email="admin@ex.com", senha=SENHA):
    return cliente.post("/", data={"email": email, "senha": senha}, follow_redirects=False)


@pytest.fixture()
def admin(cliente):
    entrar(cliente, "admin@ex.com")
    return cliente


@pytest.fixture()
def operador(app):
    c = app.test_client()
    entrar(c, "op@ex.com")
    return c


def arquivo(conteudo: bytes, nome="foto.png"):
    return (io.BytesIO(conteudo), nome)
