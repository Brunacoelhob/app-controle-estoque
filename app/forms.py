from datetime import date

from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import Email, InputRequired, Length, NumberRange, ValidationError

from .extensions import db
from .models import PERFIL_ADMIN, PERFIL_COMUM, Usuario

LIMITE_QUANTIDADE = 1_000_000


def _sem_espacos(valor):
    return valor.strip() if isinstance(valor, str) else valor


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=100)], filters=[_sem_espacos])
    senha = PasswordField("Senha", validators=[InputRequired(), Length(max=128)])


class ProdutoForm(FlaskForm):
    nome = StringField("Nome do Produto", validators=[InputRequired(), Length(max=100)], filters=[_sem_espacos])
    quantidade = IntegerField("Quantidade", validators=[InputRequired(), NumberRange(min=0, max=LIMITE_QUANTIDADE)])
    minimo = IntegerField("Mínimo em Estoque", validators=[InputRequired(), NumberRange(min=1, max=LIMITE_QUANTIDADE)])


class UsuarioForm(FlaskForm):
    nome = StringField("Nome", validators=[InputRequired(), Length(max=100)], filters=[_sem_espacos])
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=100)], filters=[_sem_espacos])
    senha = PasswordField("Senha", validators=[InputRequired(), Length(min=8, max=128)])
    perfil = SelectField(
        "Perfil",
        choices=[(PERFIL_ADMIN, "Administrador"), (PERFIL_COMUM, "Comum")],
        validators=[InputRequired()],
    )
    submit = SubmitField("Cadastrar")

    def validate_email(self, campo):
        existe = db.session.execute(db.select(Usuario.id_usuario).filter_by(Email_usuario=campo.data.lower())).first()
        if existe:
            raise ValidationError("Já existe um usuário com este e-mail.")


def nao_futura(_form, campo):
    if campo.data and campo.data > date.today():
        raise ValidationError("A data não pode estar no futuro.")


class MovimentacaoForm(FlaskForm):
    tipo_movimentacao = SelectField(
        "Tipo de Movimentação",
        choices=[("entrada", "Entrada"), ("saida", "Saída")],
        validators=[InputRequired()],
    )
    produto_id = SelectField("Produto", coerce=int, validators=[InputRequired()])
    quantidade = IntegerField(
        "Quantidade",
        validators=[InputRequired(), NumberRange(min=1, max=LIMITE_QUANTIDADE, message="A quantidade deve ser maior que 0")],
    )
    data = DateField("Data da Movimentação", format="%Y-%m-%d", default=date.today, validators=[InputRequired(), nao_futura])
