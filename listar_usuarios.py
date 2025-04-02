from models import db, Usuario
from app import app

with app.app_context():
    usuarios = Usuario.query.all()

    if not usuarios:
        print("Nenhum usuário encontrado.")
    else:
        print(f"{'ID':<3} {'Nome':<20} {'Email':<30} {'Perfil':<10} {'Senha (Hash)':<70}")
        print("-" * 130)
        for usuario in usuarios:
            print(f"{usuario.id:<3} {usuario.nome:<20} {usuario.email:<30} {usuario.perfil:<10} {usuario.senha}")
