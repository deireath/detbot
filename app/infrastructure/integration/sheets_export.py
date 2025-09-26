from typing import Iterable, Sequence, Mapping, Any
import gspread
import gspread.utils
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from app.infrastructure.integration.sheets_client import open_worksheet

def _chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i+size]

def ensure_header(ws: gspread.Worksheet, header: Sequence[str]):
    ws.update('1:1', [list(header)])

def clear_sheet(ws: gspread.Worksheet):
    ws.clear()

def write_rows_full(ws: gspread.Worksheet, header: Sequence[str], rows: Sequence[Sequence[Any]]):
    ensure_header(ws, header)
    if not rows:
        return
    start_row = 2
    for chunk in _chunks(rows, 500):
        end_row = start_row + len(chunk) - 1
        end_col = len(header)
        rng = gspread.utils.rowcol_to_a1(start_row, 1) + ':' + gspread.utils.rowcol_to_a1(end_row, end_col)
        ws.update(rng, chunk)
        start_row = end_row + 1

def read_all_rows(ws: gspread.Worksheet) -> list[list[str]]:
    return ws.get_all_values()

def header_map(header: Sequence[str]) -> dict[str, int]:
    return {h: i for i, h in enumerate(header)}

# --- PUSH FULL: чистим лист и полностью перезаписываем данными из SQL ---
async def push_full(conn: AsyncConnection, client: gspread.Client, spreadsheet_id: str, worksheet_name: str,
                    select_sql: str, sheet_columns: Sequence[str], clear_before_write: bool = True):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(select_sql)
        data = await cur.fetchall()

    header = list(sheet_columns)
    values = []
    for row in data:
        values.append([row.get(col) if row.get(col) is not None else "" for col in header])

    ws = open_worksheet(client, spreadsheet_id, worksheet_name)
    if clear_before_write:
        clear_sheet(ws)
    write_rows_full(ws, header, values)

# --- PUSH PARTIAL: обновить ТОЛЬКО указанные колонки по ключу; добавить новые при желании ---
async def push_partial(conn: AsyncConnection, client: gspread.Client, spreadsheet_id: str, worksheet_name: str,
                       select_sql: str, key_cols: Sequence[str], write_cols: Sequence[str], append_missing: bool = True):
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(select_sql)
        db_rows = await cur.fetchall()

    ws = open_worksheet(client, spreadsheet_id, worksheet_name)
    data = read_all_rows(ws)
    if not data:
        header = list(dict.fromkeys([*key_cols, *write_cols]))
        write_rows_full(ws, header, [])
        data = [header]

    header = data[0]
    hmap = header_map(header)

    # Добиваем недостающие столбцы (справа)
    needed = [*key_cols, *write_cols]
    added = False
    for col in needed:
        if col not in hmap:
            header.append(col); hmap[col] = len(header) - 1; added = True
    if added:
        ensure_header(ws, header)
        width = len(header)
        body = [r + [""] * (width - len(r)) for r in data[1:]]
        if body:
            ws.update(f"2:{len(body)+1}", body)

    # Индекс в листе: (k1,k2,...) -> row_number
    def key_tuple(row: Sequence[str]) -> tuple:
        return tuple((row[hmap[k]].strip() if k in hmap and hmap[k] < len(row) else "") for k in key_cols)

    index = {}
    for i, row in enumerate(data[1:], start=2):
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
            data[i-1] = row
        index[key_tuple(row)] = i

    # Готовим обновления
    from collections import defaultdict
    updates = defaultdict(list)  # row -> [(col_idx, value)]
    appends = []

    for d in db_rows:
        key = tuple(str(d.get(k, "") if d.get(k) is not None else "") for k in key_cols)
        if key in index:
            r = index[key]
            row = data[r-1]
            for col in write_cols:
                c = hmap[col] + 1  # 1-based
                val = d.get(col); val = "" if val is None else str(val)
                updates[r].append((c, val))
        else:
            if append_missing:
                new_row = [""] * len(header)
                for k in key_cols:
                    new_row[hmap[k]] = str(d.get(k, "") if d.get(k) is not None else "")
                for c in write_cols:
                    new_row[hmap[c]] = str(d.get(c, "") if d.get(c) is not None else "")
                appends.append(new_row)

    for r, cols in updates.items():
        min_c = min(c for c, _ in cols)
        max_c = max(c for c, _ in cols)
        current = data[r-1]
        if len(current) < len(header):
            current = current + [""] * (len(header) - len(current))
        row_copy = current[:]
        for c, v in cols:
            row_copy[c-1] = v
        rng = gspread.utils.rowcol_to_a1(r, min_c) + ':' + gspread.utils.rowcol_to_a1(r, max_c)
        ws.update(rng, [row_copy[min_c-1:max_c]])

    if appends:
        for chunk in _chunks(appends, 500):
            start_row = len(data) + 1
            end_row = start_row + len(chunk) - 1
            rng = gspread.utils.rowcol_to_a1(start_row, 1) + ':' + gspread.utils.rowcol_to_a1(end_row, len(header))
            ws.update(rng, chunk)
            data.extend(chunk)