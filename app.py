from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os

from forms import LoginForm, ProdutoForm, UsuarioForm, MovimentacaoForm
from models import db, Usuario, Produto
from models import Movimentacao

# Criação da aplicação Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta'

# Configuração da conexão com MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:***SENHA-REMOVIDA***@localhost/estoque'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco de dados
db.init_app(app)

# Configuração do Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Função que carrega o usuário logado
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Rota de login
@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(Email_usuario=form.email.data).first()
        if usuario and check_password_hash(usuario.Senha_usuario, form.senha.data):
            login_user(usuario)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha inválidos.', 'danger')
    return render_template('login.html', form=form)

# Rota principal (dashboard)
@app.route('/dashboard')
@login_required
def dashboard():
    produtos = Produto.query.all()
    return render_template('dashboard.html', produtos=produtos, usuario=current_user)

# Rota de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('login'))

# Rota para cadastrar produto
@app.route('/cadastrar-produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    form = ProdutoForm()
    if form.validate_on_submit():
        novo_produto = Produto(
            Nome_produto=form.nome.data,
            Quantidade_produto=form.quantidade.data,
            Minimo_produto=form.minimo.data
        )
        db.session.add(novo_produto)
        db.session.commit()
        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('cadastrar_produto.html', form=form)

# Rota para excluir produto
@app.route('/excluir/<int:produto_id>')
@login_required
def excluir_produto(produto_id):

    produto = Produto.query.get_or_404(produto_id)
    db.session.delete(produto)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('dashboard'))

# Rota para editar produto
@app.route('/editar/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def editar_produto(produto_id):

    produto = Produto.query.get_or_404(produto_id)
    form = ProdutoForm(obj=produto)

    if form.validate_on_submit():
        produto.Nome_produto = form.nome.data
        produto.Quantidade_produto = form.quantidade.data
        produto.Minimo_produto = form.minimo.data
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('editar_produto.html', form=form, produto=produto)

# Rota para cadastrar usuário
@app.route('/cadastrar-usuario', methods=['GET', 'POST'])
@login_required
def cadastrar_usuario():
    if current_user.Perfil_usuario != 'admin':
        flash('Apenas administradores podem cadastrar usuários.', 'danger')
        return redirect(url_for('dashboard'))

    form = UsuarioForm()

    if form.validate_on_submit():
        novo_usuario = Usuario(
            Nome_usuario=form.nome.data,
            Email_usuario=form.email.data,
            Senha_usuario=generate_password_hash(form.senha.data),
            Perfil_usuario=form.perfil.data,
            foto_url='default.png'
        )

        db.session.add(novo_usuario)
        db.session.commit()
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('cadastrar_usuario.html', form=form)


@app.route('/editar-foto', methods=['POST'])
@login_required
def editar_foto():
    file = request.files.get('foto')  # 'foto' é o name do campo do input no HTML

    if file and file.filename:
        filename = secure_filename(file.filename)
        caminho = os.path.join('static', 'imagens', filename)

        # Garante que a pasta existe
        os.makedirs(os.path.dirname(caminho), exist_ok=True)

        # Salva o arquivo na pasta
        file.save(caminho)

        # Atualiza a foto do usuário atual
        current_user.foto_url = filename
        db.session.commit()

        flash('Foto atualizada com sucesso!', 'success')
    else:
        flash('Nenhuma foto selecionada.', 'danger')

    return redirect(url_for('dashboard'))

@app.route('/movimentar-estoque', methods=['GET', 'POST'])
@login_required
def movimentar_estoque():
    form = MovimentacaoForm()
    form.produto_id.choices = [(p.id_produto, p.Nome_produto) for p in Produto.query.all()]

    if form.validate_on_submit():
        produto = Produto.query.get(form.produto_id.data)
        tipo = form.tipo_movimentacao.data
        quantidade = form.quantidade.data
        data_mov = form.data.data

        if tipo == 'entrada':
            produto.Quantidade_produto += quantidade
        elif tipo == 'saida':
            if produto.Quantidade_produto < quantidade:
                flash('Estoque insuficiente para saída.', 'danger')
                return redirect(url_for('movimentar_estoque'))
            produto.Quantidade_produto -= quantidade

        movimentacao = Movimentacao(
            tipo_movimentacao=tipo,
            quantidade=quantidade,
            data=data_mov,
            TBL_USUARIO_id=current_user.id_usuario,
            TBL_PRODUTO_id_produto=produto.id_produto
        )

        db.session.add(movimentacao)
        db.session.commit()
        flash('Movimentação registrada com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('movimentar_estoque.html', form=form)

@app.route('/painel-estoque')
@login_required
def painel_estoque():
    return render_template('painel_estoque.html', usuario=current_user)

# Inicia o servidor
if __name__ == '__main__':
    app.run(debug=True)
