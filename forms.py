from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SelectField, SubmitField
from wtforms.validators import InputRequired, NumberRange, Email, Length
from wtforms.validators import InputRequired, Email

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    senha = PasswordField('Senha', validators=[InputRequired()])

class ProdutoForm(FlaskForm):
    nome = StringField('Nome do Produto', validators=[InputRequired()])
    quantidade = IntegerField('Quantidade', validators=[InputRequired(), NumberRange(min=0)])
    minimo = IntegerField('Mínimo em Estoque', validators=[InputRequired(), NumberRange(min=1)])

class UsuarioForm(FlaskForm):
    nome = StringField('Nome', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    senha = PasswordField('Senha', validators=[InputRequired(), Length(min=6)])
    perfil = SelectField('Perfil', choices=[('admin', 'Administrador'), ('comum', 'Comum')], validators=[InputRequired()])
    submit = SubmitField('Cadastrar')
