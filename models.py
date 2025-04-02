from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Tabela de Usuários
class Usuario(db.Model, UserMixin):
    __tablename__ = 'TBL_USUARIO'

    id_usuario = db.Column(db.Integer, primary_key=True)
    Nome_usuario = db.Column(db.String(100), nullable=False)
    Email_usuario = db.Column(db.String(100), unique=True, nullable=False)
    Senha_usuario = db.Column(db.String(255), nullable=False)
    Perfil_usuario = db.Column(db.String(45), nullable=False)
    foto_url = db.Column(db.String(255), default='default.png')  # Caminho da imagem de perfil

    def get_id(self):
        return str(self.id_usuario)

# Tabela de Produtos
class Produto(db.Model):
    __tablename__ = 'TBL_PRODUTO'

    id_produto = db.Column(db.Integer, primary_key=True)
    Nome_produto = db.Column(db.String(100), nullable=False)
    Quantidade_produto = db.Column(db.Integer, default=0)
    Minimo_produto = db.Column(db.Integer, default=1)

# Tabela de Movimentações
class Movimentacao(db.Model):
    __tablename__ = 'TBL_MOVIMENTACAO'

    id_movimentacao = db.Column(db.Integer, primary_key=True)
    Tipo_movimentacao = db.Column(db.String(100), nullable=False)
    Quantidade = db.Column(db.Integer, nullable=False)
    Data = db.Column(db.Date, nullable=False)

    TBL_USUARIO_id = db.Column(db.Integer, db.ForeignKey('TBL_USUARIO.id_usuario'))
    TBL_PRODUTO_id_produto = db.Column(db.Integer, db.ForeignKey('TBL_PRODUTO.id_produto'))

    usuario = db.relationship('Usuario', backref='movimentacoes')
    produto = db.relationship('Produto', backref='movimentacoes')
