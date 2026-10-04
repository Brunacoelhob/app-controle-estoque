"""Ponto de entrada para servidores WSGI e para o CLI do Flask: `flask --app wsgi ...` / `gunicorn wsgi:app`."""

from app import create_app

app = create_app()
