import os, json

from config.config import load_config
from app.infrastructure.integration.sheets_client import make_gspread_client_from_file
from app.infrastructure.integration.sheets_export import push_full, push_partial
from app.infrastructure.integration.sheets_import import import_all_from_config as pull_import

async def sync_all(pg_pool):
    cfg = load_config()

    # читаем конфиг sync (entries)
    if cfg.google.sync_path:
        with open(cfg.google.sync_path, "r", encoding="utf-8") as f:
            sync_cfg = json.load(f)
    else:
        raise RuntimeError("Provide GSHEETS_SYNC_PATH or GSHEETS_SYNC_JSON")

    entries = sync_cfg.get("entries", [])
    if not entries:
        return []

    client = make_gspread_client_from_file(cfg.google.sa_json_path, write=True)
    results = []

    for e in entries:
        mode = e["mode"]

        if mode == "push_full":
            spreadsheet_id = e["spreadsheet_id"]
            worksheet = e.get("worksheet")
            select_sql = e["select_sql"]
            sheet_columns = e["sheet_columns"]
            clear = bool(e.get("clear_before_write", True))
            async with pg_pool.connection() as conn:
                await push_full(conn, client, spreadsheet_id, worksheet, select_sql, sheet_columns, clear)
            results.append(("push_full", worksheet or "sheet1", "ok"))

        elif mode == "push_partial":
            spreadsheet_id = e["spreadsheet_id"]
            worksheet = e.get("worksheet")
            select_sql = e["select_sql"]
            key = e["key"]
            write_cols = e["write_columns"]
            append_missing = bool(e.get("append_missing", True))
            delete_missing = bool(e.get("delete_missing", False))
            async with pg_pool.connection() as conn:
                await push_partial(conn, client, spreadsheet_id, worksheet, select_sql, key, write_cols, append_missing, delete_missing)
            results.append(("push_partial", worksheet or "sheet1", "ok"))

        elif mode == "pull_upsert":
            # Чтобы переиспользовать наш pull-сервис, временно соберём sources-json с одним источником:
            tmp_sources = {"sources": [e]}
            old = os.environ.get("GSHEETS_SOURCES_JSON")
            os.environ["GSHEETS_SOURCES_JSON"] = json.dumps(tmp_sources, ensure_ascii=False)
            try:
                await pull_import(pg_pool)
                results.append(("pull_upsert", e.get("worksheet") or "sheet1", "ok"))
            finally:
                if old is None:
                    os.environ.pop("GSHEETS_SOURCES_JSON", None)
                else:
                    os.environ["GSHEETS_SOURCES_JSON"] = old
        else:
            results.append((mode, e.get("worksheet"), "unknown_mode"))

    return results
    