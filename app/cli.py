"""Comandos de administração: flask criar-admin · flask listar-usuarios."""

from __future__ import annotations

import click
from werkzeug.security import generate_password_hash

from .extensions import db
from .models import PERFIL_ADMIN, Usuario


def registrar_comandos(app) -> None:
    @app.cli.command("criar-admin")
    @click.option("--nome", prompt="Nome")
    @click.option("--email", prompt="E-mail")
    @click.password_option("--senha", prompt="Senha", confirmation_prompt=True)
    def criar_admin(nome: str, email: str, senha: str) -> None:
        """Cria um administrador. A senha é digitada sem eco; nada de senha padrão no código."""
        email = email.strip().lower()
        if len(senha) < 8:
            raise click.ClickException("A senha deve ter pelo menos 8 caracteres.")
        if db.session.execute(db.select(Usuario).filter_by(Email_usuario=email)).first():
            raise click.ClickException(f"Já existe um usuário com o e-mail {email}.")
        db.session.add(
            Usuario(
                Nome_usuario=nome.strip(),
                Email_usuario=email,
                Senha_usuario=generate_password_hash(senha),
                Perfil_usuario=PERFIL_ADMIN,
            )
        )
        db.session.commit()
        click.echo("Administrador criado com sucesso.")

    @app.cli.command("listar-usuarios")
    def listar_usuarios() -> None:
        """Lista usuários (sem mostrar hashes de senha)."""
        usuarios = db.session.execute(db.select(Usuario).order_by(Usuario.id_usuario)).scalars().all()
        if not usuarios:
            click.echo("Nenhum usuário cadastrado. Crie o primeiro com: flask criar-admin")
            return
        click.echo(f"{'ID':<4} {'Nome':<24} {'E-mail':<34} Perfil")
        for u in usuarios:
            click.echo(f"{u.id_usuario:<4} {u.Nome_usuario:<24} {u.Email_usuario:<34} {u.Perfil_usuario}")
