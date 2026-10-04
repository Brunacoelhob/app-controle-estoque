from flask_login import UserMixin
from sqlalchemy import CheckConstraint

from .extensions import db

PERFIL_ADMIN = "admin"
PERFIL_COMUM = "comum"
TIPOS_MOVIMENTACAO = ("entrada", "saida")


class Usuario(db.Model, UserMixin):
    __tablename__ = "TBL_USUARIO"
    __table_args__ = (CheckConstraint(f"Perfil_usuario IN ('{PERFIL_ADMIN}', '{PERFIL_COMUM}')", name="ck_usuario_perfil"),)

    id_usuario = db.Column(db.Integer, primary_key=True)
    Nome_usuario = db.Column(db.String(100), nullable=False)
    Email_usuario = db.Column(db.String(100), unique=True, nullable=False)
    Senha_usuario = db.Column(db.String(255), nullable=False)
    Perfil_usuario = db.Column(db.String(45), nullable=False, default=PERFIL_COMUM)
    foto_url = db.Column(db.String(255))  # nome do arquivo em UPLOAD_DIR; vazio = sem foto

    def get_id(self) -> str:
        return str(self.id_usuario)

    @property
    def is_admin(self) -> bool:
        return self.Perfil_usuario == PERFIL_ADMIN


class Produto(db.Model):
    __tablename__ = "TBL_PRODUTO"
    __table_args__ = (
        CheckConstraint("Quantidade_produto >= 0", name="ck_produto_quantidade"),
        CheckConstraint("Minimo_produto >= 0", name="ck_produto_minimo"),
    )

    id_produto = db.Column(db.Integer, primary_key=True)
    Nome_produto = db.Column(db.String(100), nullable=False)
    Quantidade_produto = db.Column(db.Integer, nullable=False, default=0)
    Minimo_produto = db.Column(db.Integer, nullable=False, default=1)

    @property
    def abaixo_do_minimo(self) -> bool:
        return self.Quantidade_produto < self.Minimo_produto


class Movimentacao(db.Model):
    __tablename__ = "TBL_MOVIMENTACAO"
    __table_args__ = (
        CheckConstraint("tipo_movimentacao IN ('entrada', 'saida')", name="ck_mov_tipo"),
        CheckConstraint("quantidade > 0", name="ck_mov_quantidade"),
    )

    id_movimentacao = db.Column(db.Integer, primary_key=True)
    tipo_movimentacao = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Date, nullable=False)

    TBL_USUARIO_id = db.Column(db.Integer, db.ForeignKey("TBL_USUARIO.id_usuario"), nullable=False)
    TBL_PRODUTO_id_produto = db.Column(db.Integer, db.ForeignKey("TBL_PRODUTO.id_produto"), nullable=False)

    usuario = db.relationship("Usuario", backref="movimentacoes")
    produto = db.relationship("Produto", backref="movimentacoes")

    def __repr__(self) -> str:
        return f"<Movimentacao {self.id_movimentacao} {self.tipo_movimentacao} x{self.quantidade}>"
