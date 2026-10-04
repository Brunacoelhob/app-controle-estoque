# Controle de Estoque (Flask + MySQL)

[![CI](https://github.com/Brunacoelhob/app-controle-estoque/actions/workflows/ci.yml/badge.svg)](https://github.com/Brunacoelhob/app-controle-estoque/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

Sistema web para controlar o estoque de produtos: cadastro, movimentações de entrada e saída, alerta de estoque abaixo do mínimo, painel com gráficos e dois perfis de acesso (administrador e comum).

## Funcionalidades

- Login com perfis **administrador** (gerencia produtos e usuários) e **comum** (consulta e movimenta estoque)
- Cadastro, edição e exclusão de produtos; destaque dos que estão abaixo do mínimo
- Entradas e saídas com histórico (quem, quando e quanto); a saída nunca deixa o saldo negativo
- Painel com **dados reais**: estoque x mínimo, produtos em falta, entradas/saídas por dia e movimentação por usuário
- Foto de perfil

## Como executar

### Com Docker (recomendado)

```bash
cp .env.example .env                                       # defina SECRET_KEY e DB_PASSWORD
docker compose up -d --build --wait
docker compose exec app flask --app wsgi criar-admin       # cria o primeiro administrador (pede a senha)
```

Acesse http://localhost:8000. As migrações do banco são aplicadas automaticamente na subida.

### Sem Docker (SQLite local)

```bash
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
flask --app wsgi db upgrade
flask --app wsgi criar-admin
flask --app wsgi run
```

Para usar MySQL, defina `DATABASE_URL=mysql+pymysql://usuario:senha@host:3306/estoque?charset=utf8mb4`.

## Arquitetura

```
app/
├── __init__.py     fábrica da aplicação (create_app) + cabeçalhos de segurança
├── config.py       configuração por ambiente (SECRET_KEY obrigatória)
├── models.py       tabelas, com restrições (CHECK) no banco
├── forms.py        validação dos formulários
├── servicos.py     regras: movimentação atômica, painel, upload de foto
├── routes.py       rotas e permissões
├── cli.py          flask criar-admin · flask listar-usuarios
├── templates/ · static/
migrations/         migrações do banco (Alembic)
tests/              56 testes
```

## Segurança e correções em relação à primeira versão

| Problema na versão anterior | Correção |
|---|---|
| Senha do MySQL (`root`) e `SECRET_KEY = 'sua_chave_secreta'` no código | Variáveis de ambiente; o app **não sobe** sem `SECRET_KEY` |
| `debug=True` (console remoto do Werkzeug = execução de código) | Servidor de produção (gunicorn); sem debug |
| Excluir produto por **GET** (`/excluir/1`): um link/imagem em outro site apagava dados | Somente POST com token CSRF e confirmação |
| Qualquer usuário logado apagava/editava produtos | Apenas administradores; demais recebem 403 |
| Upload de foto aceitava qualquer arquivo com o nome original em `static/` (um `.html` virava XSS armazenado; nomes repetidos sobrescreviam fotos) | Valida pelo **conteúdo** (PNG/JPEG/GIF/WEBP), nome aleatório, limite de 2 MB, fora de `static/`, servido só a usuários logados |
| Saída de estoque lia o saldo e gravava depois (dois usuários ao mesmo tempo → saldo negativo) | Um único `UPDATE ... WHERE quantidade >= :q` decide no banco |
| Painel com números e vendedores **inventados** (R$ 12.500, "Bruna", "Caio") | Painel calculado a partir do banco |
| Erros de validação dos formulários não apareciam (e-mail repetido, quantidade negativa) | Mensagens exibidas ao usuário |
| `criar_usuario.py` criava admin com senha fixa `123456789` | `flask criar-admin` pede a senha, sem eco |
| `listar_usuarios.py` quebrado e imprimia hashes de senha | `flask listar-usuarios` sem hashes |
| Login sem limite de tentativas; resposta/tempo revelavam e-mails existentes | 10 tentativas/min por IP, mensagem única e tempo igual |
| Sem CSP, cookies sem `HttpOnly/SameSite`, scripts inline | Cabeçalhos de segurança, cookies endurecidos, JS em arquivos |
| `.pyc`, banco SQLite e fotos de pessoas versionados | Removidos; `.gitignore` adequado |
| Excluir produto com histórico gerava erro 500 | Recusa com mensagem clara |
| Sem testes, sem migrações, sem Docker, sem CI | 56 testes, Alembic, Docker Compose e CI |

## Testes

```bash
pip install -r requirements-dev.txt
pytest
ruff check . && ruff format --check .
```

## Limitações conhecidas

- O limitador de tentativas guarda contagens em memória (adequado a 1 instância; use Redis para várias).
- Sem recuperação de senha por e-mail nem gestão de usuários além do cadastro.
- Os gráficos usam Chart.js via CDN (liberada na política de segurança).

## Licença

[MIT](LICENSE)
