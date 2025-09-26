from typing import Sequence, Mapping
from psycopg import AsyncConnection
from psycopg import sql

def _build_upsert_query(table: str, db_cols: Sequence[str], pk_cols: Sequence[str]):
    cols = [sql.Identifier(c) for c in db_cols]
    insert = sql.SQL("INSERT INTO {table} ({cols}) VALUES ({vals})").format(
        table=sql.SQL(table),
        cols=sql.SQL(", ").join(cols),
        vals=sql.SQL(", ").join([sql.Placeholder(c) for c in db_cols])
    )
    set_pairs = [sql.SQL("{c}=EXCLUDED.{c}").format(c=sql.Identifier(c)) for c in db_cols if c not in pk_cols]
    conflict = sql.SQL(" ON CONFLICT ({pk}) DO UPDATE SET {set}").format(
    pk=sql.SQL(", ").join(sql.Identifier(c) for c in pk_cols),
    set=sql.SQL(", ").join(set_pairs) if set_pairs else sql.SQL("NOTHING")
    )
    return insert + conflict

async def bulk_upsert(conn: AsyncConnection, table: str, rows: Sequence[Mapping], pk_cols: Sequence[str]):
    if not rows:
        return 0
    db_cols = list(rows[0].keys())
    q = _build_upsert_query(table, db_cols, pk_cols)
    async with conn.cursor() as cur:
        await cur.executemany(q, rows)
    return len(rows)