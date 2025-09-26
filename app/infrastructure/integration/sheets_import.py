import asyncio, json
import logging
from datetime import datetime
from typing import Any
from config.config import load_config
from app.infrastructure.integration.sheets_client import make_gspread_client_from_file, fetch_values
from app.infrastructure.integration.bulk_upsert import bulk_upsert

def _norm(s: str) -> str:
    return s.strip().lower().replace(" ","_")

def _cast(v: str | None, kind: str | None):
    if v is None or v == "":
        return None
    kind = (kind or "").lower()
    if kind in ("int", "integer"):
        try: 
            return int(str(v).strip())
        except: 
            return None
    if kind in ("float","numeric","double"):
        try: 
            return float(str(v).replace(",", "."))
        except:
            return None
    if kind in ("bool","boolean"):
        return str(v).strip().lower() in {"1","true","yes","y","да","истина"}
    if kind in ("datetime","timestamp"):
        try:
            return datetime.fromisoformat(str(v).strip())
        except:
            return None
    return str(v)

def _map_and_cast(header: list[str], row: list[str], col_map: dict[str,str], casts: dict[str,str]) -> dict[str, Any]:
    src = { _norm(h): (row[i] if i < len(row) else None) for i, h in enumerate(header) }
    out: dict[str, Any] = {}
    for sheet_col, db_col in col_map.items():
        key = _norm(sheet_col)
        out[db_col] = _cast(src.get(key), casts.get(sheet_col) if casts else None)
    return out

async def import_all_from_config(pg_pool) -> list[tuple[str, int]]:
    cfg = load_config()
    if cfg.google.sources_path:
        with open(cfg.google.sources_path, "r", encoding="utf-8") as f:
            sources_cfg = json.load(f)
    else:
        raise RuntimeError("Provide GSHEETS_SOURCES_PATH or GSHEETS_SOURCES_JSON")

    sources = sources_cfg.get("sources", [])
    if not sources:
        return []

    client = make_gspread_client_from_file(cfg.google.sa_json_path, write=False)
    loop = asyncio.get_running_loop()

    results: list[tuple[str, int]] = []

    for s in sources:
        spreadsheet_id: str = s["spreadsheet_id"]
        worksheet: str | None = s.get("worksheet")
        rng: str = s.get("range", "A:Z")
        table: str = s["table"]
        pk: list[str] = s["pk"]
        col_map: dict[str,str] = s.get("columns", {})
        casts: dict[str,str] = s.get("casts", {})


        values = await loop.run_in_executor(None, lambda: fetch_values(client, spreadsheet_id, worksheet, rng))
        if not values:
            results.append((table, 0))
            continue

        header, *rows = values
        header = [str(h) for h in header]
        logger = logging.getLogger(__name__)
        logger.info("[pull_upsert] sheet=%s header=%s rows=%d", worksheet or "sheet1", header, len(rows))

        if not col_map:
            col_map = { h: _norm(h) for h in header }

        if not set(col_map.keys()).issubset(set(header)):
            missing = set(col_map.keys()) - set(header)
            raise RuntimeError(f"[{table}] Missing columns in sheet: {missing}")

        prepared = []
        skipped_empty_pk = 0 
        for r in rows:
            d = _map_and_cast(header, r, col_map, casts)
            if any(d.get(k) in (None, "") for k in pk):
                skipped_empty_pk += 1
                continue
            prepared.append(d)
        
        logger.info("[pull_upsert] table=%s prepared=%d skipped_empty_pk=%d", table, len(prepared), skipped_empty_pk)

        if not prepared:
            results.append((table, 0))
            continue

        async with pg_pool.connection() as conn:
            n = await bulk_upsert(conn, table, prepared, pk)
        results.append((table, n))

    return results