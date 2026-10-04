"""Regras de negócio, separadas das rotas (para serem testadas sem HTTP)."""

from __future__ import annotations

import re
import uuid
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import func, update

from .extensions import db
from .models import Movimentacao, Produto, Usuario


class EstoqueInsuficiente(Exception):
    pass


class ProdutoNaoEncontrado(Exception):
    pass


class ProdutoComHistorico(Exception):
    """Produto que já teve movimentações não pode ser apagado (perderia o histórico)."""


def movimentar(produto_id: int, tipo: str, quantidade: int, data: date, usuario_id: int) -> Produto:
    """Registra entrada/saída de forma ATÔMICA.

    A baixa é um único UPDATE condicional (`... WHERE quantidade >= :q`): o banco decide se há saldo.
    Antes o código lia a quantidade, comparava em Python e gravava depois; dois usuários saindo com o
    mesmo produto ao mesmo tempo podiam deixar o estoque negativo (condição de corrida).
    """
    if tipo not in ("entrada", "saida"):
        raise ValueError("Tipo de movimentação inválido.")
    if quantidade < 1:
        raise ValueError("A quantidade deve ser maior que zero.")
    if db.session.get(Produto, produto_id) is None:
        raise ProdutoNaoEncontrado(produto_id)

    coluna = Produto.Quantidade_produto
    if tipo == "entrada":
        passo = update(Produto).where(Produto.id_produto == produto_id).values(Quantidade_produto=coluna + quantidade)
    else:
        passo = (
            update(Produto)
            .where(Produto.id_produto == produto_id, coluna >= quantidade)
            .values(Quantidade_produto=coluna - quantidade)
        )
    if db.session.execute(passo).rowcount == 0:
        db.session.rollback()
        raise EstoqueInsuficiente(produto_id)

    db.session.add(
        Movimentacao(
            tipo_movimentacao=tipo,
            quantidade=quantidade,
            data=data,
            TBL_USUARIO_id=usuario_id,
            TBL_PRODUTO_id_produto=produto_id,
        )
    )
    db.session.commit()
    produto = db.session.get(Produto, produto_id)
    db.session.refresh(produto)
    return produto


def excluir_produto(produto_id: int) -> None:
    produto = db.session.get(Produto, produto_id)
    if produto is None:
        raise ProdutoNaoEncontrado(produto_id)
    tem_historico = db.session.execute(
        db.select(Movimentacao.id_movimentacao).filter_by(TBL_PRODUTO_id_produto=produto_id).limit(1)
    ).first()
    if tem_historico:
        raise ProdutoComHistorico(produto_id)
    db.session.delete(produto)
    db.session.commit()


def dados_do_painel(hoje: date | None = None, dias: int = 30) -> dict:
    """Números REAIS do estoque (a versão anterior exibia valores fixos inventados, como 'Total Vendido R$ 12.500')."""
    hoje = hoje or date.today()
    inicio = hoje - timedelta(days=dias - 1)

    produtos = db.session.execute(db.select(Produto).order_by(Produto.Nome_produto)).scalars().all()
    abaixo = [p for p in produtos if p.abaixo_do_minimo]

    # Movimentações por dia e tipo, no período.
    linhas = db.session.execute(
        db.select(Movimentacao.data, Movimentacao.tipo_movimentacao, func.sum(Movimentacao.quantidade))
        .where(Movimentacao.data >= inicio, Movimentacao.data <= hoje)
        .group_by(Movimentacao.data, Movimentacao.tipo_movimentacao)
    ).all()
    por_dia: dict[date, dict[str, int]] = {}
    for dia, tipo, total in linhas:
        por_dia.setdefault(dia, {"entrada": 0, "saida": 0})[tipo] = int(total)

    datas = [inicio + timedelta(days=i) for i in range(dias)]
    entradas = [por_dia.get(d, {}).get("entrada", 0) for d in datas]
    saidas = [por_dia.get(d, {}).get("saida", 0) for d in datas]

    por_usuario = db.session.execute(
        db.select(Usuario.Nome_usuario, func.sum(Movimentacao.quantidade))
        .join(Movimentacao, Movimentacao.TBL_USUARIO_id == Usuario.id_usuario)
        .where(Movimentacao.data >= inicio, Movimentacao.data <= hoje)
        .group_by(Usuario.id_usuario, Usuario.Nome_usuario)
        .order_by(func.sum(Movimentacao.quantidade).desc())
    ).all()

    return {
        "resumo": {
            "produtos": len(produtos),
            "unidades": sum(p.Quantidade_produto for p in produtos),
            "abaixo_do_minimo": len(abaixo),
            "entradas_periodo": sum(entradas),
            "saidas_periodo": sum(saidas),
            "dias": dias,
        },
        "estoque": {
            "rotulos": [p.Nome_produto for p in produtos],
            "quantidade": [p.Quantidade_produto for p in produtos],
            "minimo": [p.Minimo_produto for p in produtos],
        },
        "faltantes": {
            "rotulos": [p.Nome_produto for p in abaixo],
            "deficit": [p.Minimo_produto - p.Quantidade_produto for p in abaixo],
        },
        "movimentacao": {
            "rotulos": [d.strftime("%d/%m") for d in datas],
            "entradas": entradas,
            "saidas": saidas,
        },
        "por_usuario": {
            "rotulos": [nome for nome, _ in por_usuario],
            "unidades": [int(total) for _, total in por_usuario],
        },
    }


# ---------------------------------------------------------------- upload de foto
_ASSINATURAS = (
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
)
NOME_DE_FOTO_VALIDO = re.compile(r"^[0-9a-f]{32}\.(png|jpg|gif|webp)$")


class FotoInvalida(ValueError):
    pass


def _extensao_pelo_conteudo(inicio: bytes) -> str | None:
    """Descobre o tipo pelos primeiros bytes do arquivo (a extensão enviada pelo cliente pode mentir)."""
    for assinatura, extensao in _ASSINATURAS:
        if inicio.startswith(assinatura):
            return extensao
    if inicio[:4] == b"RIFF" and inicio[8:12] == b"WEBP":
        return ".webp"
    return None


def salvar_foto(arquivo, pasta: Path) -> str:
    """Valida pelo CONTEÚDO (não pelo nome), gera um nome aleatório e grava. Devolve o nome salvo.

    Antes qualquer arquivo era salvo com o nome original dentro de static/: um '.html' enviado ali seria
    servido ao navegador (XSS armazenado) e nomes repetidos sobrescreviam fotos de outras pessoas.
    """
    inicio = arquivo.stream.read(16)
    arquivo.stream.seek(0)
    extensao = _extensao_pelo_conteudo(inicio)
    if extensao is None:
        raise FotoInvalida("Envie uma imagem PNG, JPEG, GIF ou WEBP.")
    nome = uuid.uuid4().hex + extensao
    arquivo.save(pasta / nome)
    return nome
