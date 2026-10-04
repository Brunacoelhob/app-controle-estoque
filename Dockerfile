# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuário sem privilégios; /data guarda as fotos enviadas (monte um volume nele).
RUN useradd --system --uid 10001 app && mkdir -p /data/uploads && chown -R app /data
USER app
ENV UPLOAD_DIR=/data/uploads

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=30s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/saude', timeout=2).status == 200 else 1)"

# Aplica as migrações do banco e sobe o servidor de produção (gunicorn).
CMD ["sh", "-c", "flask --app wsgi db upgrade && exec gunicorn --bind 0.0.0.0:8000 --workers 2 wsgi:app"]
