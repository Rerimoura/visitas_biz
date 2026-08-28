# clientes_db.py — consulta de dados cadastrais do cliente no Postgres (tabela `clientes`)
# Sem dependência do Streamlit — recebe a config de conexão como parâmetro.

import psycopg2


def get_connection(pg_config: dict):
    return psycopg2.connect(
        host=pg_config["host"],
        dbname=pg_config["database"],
        user=pg_config["user"],
        password=pg_config["password"],
        port=pg_config["port"],
        sslmode="require",
        connect_timeout=10,
    )


def _status_cliente(antecipado: str | None, situacao: str | None) -> str:
    if (antecipado or "").strip().upper() == "A28":
        return "Antecipado"
    if (situacao or "").strip().upper() == "A":
        return "Liberado"
    return "Suspenso"


def buscar_cliente(conn, cnpj: str, codigo: str) -> dict | None:
    """Busca dados cadastrais do cliente por CNPJ ou código interno (coluna `cliente`).
    Retorna None se nenhum dos dois foi informado ou se não encontrar o cliente."""
    cnpj_digits = "".join(ch for ch in (cnpj or "") if ch.isdigit())
    codigo_digits = "".join(ch for ch in (codigo or "") if ch.isdigit())

    cnpj_param = int(cnpj_digits) if cnpj_digits else None
    codigo_param = int(codigo_digits) if codigo_digits else None

    if cnpj_param is None and codigo_param is None:
        return None

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT raz_social, fantasia, cidade, bairro, endereco, antecipado, situacao, limite_aberto
            FROM clientes
            WHERE cnpj = %(cnpj)s OR cliente = %(codigo)s
            LIMIT 1
            """,
            {"cnpj": cnpj_param, "codigo": codigo_param},
        )
        row = cur.fetchone()

    if not row:
        return None

    raz_social, fantasia, cidade, bairro, endereco, antecipado, situacao, limite_aberto = row
    return {
        "razao_social": raz_social or "",
        "nome_fantasia": fantasia or "",
        "cidade": cidade or "",
        "bairro": bairro or "",
        "endereco": endereco or "",
        "status": _status_cliente(antecipado, situacao),
        "limite": float(limite_aberto) if limite_aberto is not None else None,
    }


def _resolver_cliente_id(conn, cnpj: str, codigo: str) -> int | None:
    """Resolve o ID interno do cliente (coluna `cliente`, usada em `vendas`)
    a partir do código informado diretamente ou, se só houver CNPJ, buscando
    o cadastro correspondente."""
    codigo_digits = "".join(ch for ch in (codigo or "") if ch.isdigit())
    if codigo_digits:
        return int(codigo_digits)

    cnpj_digits = "".join(ch for ch in (cnpj or "") if ch.isdigit())
    if not cnpj_digits:
        return None

    with conn.cursor() as cur:
        cur.execute("SELECT cliente FROM clientes WHERE cnpj = %s LIMIT 1", (int(cnpj_digits),))
        row = cur.fetchone()
    return row[0] if row else None


def buscar_ultima_venda(conn, cnpj: str, codigo: str) -> str | None:
    """Retorna a data (YYYY-MM-DD) da venda mais recente desse cliente —
    de qualquer vendedor da BIZ, não só de quem está preenchendo o
    relatório (tabela `vendas`, tipo='V' — exclui devoluções; vendedor 2
    é excluído por não representar um vendedor real)."""
    cliente_id = _resolver_cliente_id(conn, cnpj, codigo)
    if cliente_id is None:
        return None

    with conn.cursor() as cur:
        cur.execute(
            "SELECT MAX(data_emissao) FROM vendas WHERE cliente = %s AND tipo = 'V' AND vendedor <> 2",
            (cliente_id,),
        )
        row = cur.fetchone()

    if not row or row[0] is None:
        return None
    return row[0].isoformat()
