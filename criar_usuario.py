from werkzeug.security import generate_password_hash
from models import db, Usuario
from app import app

with app.app_context():
    senha_hash = generate_password_hash('123456789')  # Substitua '123456789' pela senha desejada
    novo_usuario = Usuario(
        Nome_usuario='user',
        Email_usuario='brunacoelho0404@gmail.com',
        Senha_usuario=senha_hash,
        Perfil_usuario='admin'
    )
    db.session.add(novo_usuario)
    db.session.commit()
    print('Usuário criado com sucesso!')
