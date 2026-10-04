from __future__ import annotations

from functools import wraps

from flask import abort, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from . import servicos
from .config import pasta_de_uploads
from .extensions import db
from .forms import LoginForm, MovimentacaoForm, ProdutoForm, UsuarioForm
from .models import Produto, Usuario

# Hash de uma senha qualquer: usado para gastar o mesmo tempo quando o e-mail não existe, de modo que a
# resposta não revele (pelo tempo) quais e-mails têm conta.
_HASH_FALSO = generate_password_hash("senha-descartavel")


def admin_required(visao):
    """Só administradores. Antes apenas 'cadastrar usuário' era protegido: qualquer logado apagava produtos."""

    @wraps(visao)
    @login_required
    def embrulho(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return visao(*args, **kwargs)

    return embrulho


def mostrar_erros(form) -> None:
    """Os templates só exibem mensagens 'flash'; sem isto, erros de validação (e-mail repetido, quantidade
    negativa...) ficavam invisíveis e o usuário via o formulário voltar sem explicação."""
    if request.method == "POST":
        for erros in form.errors.values():
            for erro in erros:
                if erro != "CSRF token is missing." and erro != "The CSRF token is missing.":
                    flash(erro, "danger")


def registrar_rotas(app, limiter) -> None:
    @app.get("/saude")
    @limiter.exempt
    def saude():
        db.session.execute(db.text("SELECT 1"))
        return jsonify(status="ok")

    @app.errorhandler(403)
    def proibido(_erro):
        flash("Você não tem permissão para essa ação.", "danger")
        return redirect(url_for("dashboard") if current_user.is_authenticated else url_for("login")), 303

    @app.errorhandler(413)
    def grande_demais(_erro):
        flash("Arquivo muito grande (máximo 2 MB).", "danger")
        return redirect(url_for("dashboard") if current_user.is_authenticated else url_for("login")), 303

    # ------------------------------------------------------------------ autenticação
    @app.route("/", methods=["GET", "POST"])
    @limiter.limit(lambda: current_app.config["LIMITE_LOGIN"], methods=["POST"])  # freia tentativas de adivinhar senha
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = LoginForm()
        if form.validate_on_submit():
            usuario = db.session.execute(db.select(Usuario).filter_by(Email_usuario=form.email.data.lower())).scalar()
            senha_ok = check_password_hash(usuario.Senha_usuario if usuario else _HASH_FALSO, form.senha.data)
            if usuario and senha_ok:
                login_user(usuario)
                return redirect(url_for("dashboard"))
            flash("Email ou senha inválidos.", "danger")
        else:
            mostrar_erros(form)
        return render_template("login.html", form=form)

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logout realizado com sucesso!", "info")
        return redirect(url_for("login"))

    # ------------------------------------------------------------------ painel e produtos
    @app.get("/dashboard")
    @login_required
    def dashboard():
        produtos = db.session.execute(db.select(Produto).order_by(Produto.Nome_produto)).scalars().all()
        return render_template("dashboard.html", produtos=produtos, usuario=current_user)

    @app.route("/cadastrar-produto", methods=["GET", "POST"])
    @admin_required
    def cadastrar_produto():
        form = ProdutoForm()
        if form.validate_on_submit():
            db.session.add(
                Produto(Nome_produto=form.nome.data, Quantidade_produto=form.quantidade.data, Minimo_produto=form.minimo.data)
            )
            db.session.commit()
            flash("Produto cadastrado com sucesso!", "success")
            return redirect(url_for("dashboard"))
        mostrar_erros(form)
        return render_template("cadastrar_produto.html", form=form)

    @app.route("/editar/<int:produto_id>", methods=["GET", "POST"])
    @admin_required
    def editar_produto(produto_id: int):
        produto = db.get_or_404(Produto, produto_id)
        form = ProdutoForm(obj=produto)
        if request.method == "GET":
            form.nome.data, form.quantidade.data, form.minimo.data = (
                produto.Nome_produto,
                produto.Quantidade_produto,
                produto.Minimo_produto,
            )
        if form.validate_on_submit():
            produto.Nome_produto = form.nome.data
            produto.Quantidade_produto = form.quantidade.data
            produto.Minimo_produto = form.minimo.data
            db.session.commit()
            flash("Produto atualizado com sucesso!", "success")
            return redirect(url_for("dashboard"))
        mostrar_erros(form)
        return render_template("editar_produto.html", form=form, produto=produto)

    # POST (e não GET): um link ou imagem de outro site não pode apagar produtos (CSRF) nem um
    # pré-carregador de links do navegador acionar a exclusão.
    @app.post("/excluir/<int:produto_id>")
    @admin_required
    def excluir_produto(produto_id: int):
        try:
            servicos.excluir_produto(produto_id)
            flash("Produto excluído com sucesso!", "success")
        except servicos.ProdutoNaoEncontrado:
            abort(404)
        except servicos.ProdutoComHistorico:
            flash("Este produto possui movimentações e não pode ser excluído (o histórico seria perdido).", "danger")
        return redirect(url_for("dashboard"))

    # ------------------------------------------------------------------ usuários
    @app.route("/cadastrar-usuario", methods=["GET", "POST"])
    @admin_required
    def cadastrar_usuario():
        form = UsuarioForm()
        if form.validate_on_submit():
            db.session.add(
                Usuario(
                    Nome_usuario=form.nome.data,
                    Email_usuario=form.email.data.lower(),
                    Senha_usuario=generate_password_hash(form.senha.data),
                    Perfil_usuario=form.perfil.data,
                )
            )
            db.session.commit()
            flash("Usuário cadastrado com sucesso!", "success")
            return redirect(url_for("dashboard"))
        mostrar_erros(form)
        return render_template("cadastrar_usuario.html", form=form)

    @app.post("/editar-foto")
    @login_required
    def editar_foto():
        arquivo = request.files.get("foto")
        if not arquivo or not arquivo.filename:
            flash("Nenhuma foto selecionada.", "danger")
            return redirect(url_for("dashboard"))
        try:
            nome = servicos.salvar_foto(arquivo, pasta_de_uploads(current_app))
        except servicos.FotoInvalida as erro:
            flash(str(erro), "danger")
            return redirect(url_for("dashboard"))
        anterior = current_user.foto_url
        current_user.foto_url = nome
        db.session.commit()
        if anterior and servicos.NOME_DE_FOTO_VALIDO.match(anterior):
            (pasta_de_uploads(current_app) / anterior).unlink(missing_ok=True)  # não acumula fotos antigas
        flash("Foto atualizada com sucesso!", "success")
        return redirect(url_for("dashboard"))

    @app.get("/fotos/<nome>")
    @login_required
    def foto(nome: str):
        if not servicos.NOME_DE_FOTO_VALIDO.match(nome):  # bloqueia ../ e qualquer nome fora do padrão gerado
            abort(404)
        return send_from_directory(pasta_de_uploads(current_app), nome)

    # ------------------------------------------------------------------ estoque
    @app.route("/movimentar-estoque", methods=["GET", "POST"])
    @login_required
    def movimentar_estoque():
        form = MovimentacaoForm()
        produtos = db.session.execute(db.select(Produto).order_by(Produto.Nome_produto)).scalars().all()
        form.produto_id.choices = [(p.id_produto, p.Nome_produto) for p in produtos]

        if form.validate_on_submit():
            try:
                servicos.movimentar(
                    form.produto_id.data,
                    form.tipo_movimentacao.data,
                    form.quantidade.data,
                    form.data.data,
                    current_user.id_usuario,
                )
            except servicos.EstoqueInsuficiente:
                flash("Estoque insuficiente para saída.", "danger")
                return redirect(url_for("movimentar_estoque"))
            except servicos.ProdutoNaoEncontrado:
                abort(404)
            flash("Movimentação registrada com sucesso!", "success")
            return redirect(url_for("dashboard"))
        mostrar_erros(form)
        return render_template("movimentar_estoque.html", form=form)

    @app.get("/painel-estoque")
    @login_required
    def painel_estoque():
        return render_template("painel_estoque.html", usuario=current_user, dados=servicos.dados_do_painel())

    @app.get("/painel-estoque/dados")
    @login_required
    def painel_estoque_dados():
        return jsonify(servicos.dados_do_painel())
