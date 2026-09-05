# Copyright 2026 Omar Zagonel El Laden
# SPDX-License-Identifier: GPL-2.0-only

import random
import sqlite3
from typing import Annotated

import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, Response, RedirectResponse


__version__ = "0.3.0"

db_path = "db.sqlite3"

min_next_wakeup = 18*3600  # 18h
max_next_wakeup = 21*3600  # 21h

timeout_s = 60

battery_value_to_v = "/4095.0*3.3*2"

timezone = "-3 hours"


app = FastAPI(
    title="SIMPAT",
    version=__version__
)


class Alert(BaseModel):
    item_id:     int
    status:      str
    battery:     int
    boot_count:  int
    rep_wakeups: int
    bssid:       str

class Item(BaseModel):
    id:          int
    room:        str
    description: str

class AccessPoint(BaseModel):
    bssid:       str
    description: str


def create_html_table(query):
    with sqlite3.connect(db_path, timeout=timeout_s) as con:
        cur = con.cursor()
        cur.execute(query)

        list_items = cur.fetchall()
        list_headers = [d[0] for d in cur.description]

    list_html_lines = []
    for item in list_items:
        cells = "".join([f"<td>{v}</td>" for v in item])
        list_html_lines.append(f"<tr>{cells}</tr>")

    list_html_headers = []
    for i in list_headers:
        list_html_headers.append(f"<th>{i}</th>")

    html_table = f"""
    <table border="1"
           style="border-collapse: collapse; width: 98%; margin: 0 auto;"
    >        <thead>
            <tr>
                {"".join(list_html_headers)}
            </tr>
        </thead>
        <tbody>
            {"".join(list_html_lines)}
        </tbody>
    </table>
    """

    return html_table


@app.head("/", include_in_schema=False)
async def head_root():
    pass

@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    return Response(status_code=204)  # FileResponse("favicon.ico")

@app.get("/", response_class=HTMLResponse)
async def get_root():
    return await get_index()

@app.get("/index.html", response_class=HTMLResponse)
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.get("/register_item", response_class=HTMLResponse)
async def get_register_item():
    with open("register_item.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.get("/register_access_point", response_class=HTMLResponse)
async def get_register_access_point():
    with open("register_ap.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.get("/update", response_class=HTMLResponse)
async def get_update():
    with open("update.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)

@app.get("/alerts", response_class=HTMLResponse)
async def get_alerts():
    query = f"""
        SELECT *,
               ROUND(battery{battery_value_to_v}, 2) || ' V' AS _battery_v,
               datetime(datetime, '{timezone}') AS _localtime
        FROM alerts
    """
    html_table = create_html_table(query)
    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>Alertas</title>
            </head>
            <body style="text-align: center;">
                <h1>Alertas</h1>
                {html_table}
                <br><br>
                <button onclick="window.location.href='/'">Voltar</button>
            </body>
        </html>
        """
    )

@app.get("/all", response_class=HTMLResponse)
async def get_all():
    query = f"""
        SELECT al.id,
               al.item_id,
               it.description AS _item_descr,
               it.room,
               al.status,
               al.battery,
               ROUND(al.battery{battery_value_to_v}, 2) || ' V' AS _battery_v,
               al.boot_count,
               al.rep_wakeups,
               al.bssid,
               ap.description AS _ap_descr,
               nw.datetime AS _next_wakeup,
               datetime(al.datetime, '{timezone}') AS _localtime
        FROM alerts AS al
        LEFT JOIN items AS it
            ON al.item_id = it.id
        LEFT JOIN next_wakeups AS nw
            ON al.item_id = nw.item_id
        LEFT JOIN access_points AS ap
            ON al.bssid = ap.bssid
    """
    html_table = create_html_table(query)
    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>Alertas Completos</title>
            </head>
            <body style="text-align: center;">
                <h1>Alertas Completos</h1>
                {html_table}
                <br><br>
                <button onclick="window.location.href='/'">Voltar</button>
            </body>
        </html>
        """
    )

@app.get("/items", response_class=HTMLResponse)
async def get_items():
    query = "SELECT * FROM items"
    html_table = create_html_table(query)
    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>Itens</title>
            </head>
            <body style="text-align: center;">
                <h1>Itens</h1>
                {html_table}
                <br><br>
                <button onclick="window.location.href='/'">Voltar</button>
            </body>
        </html>
        """
    )

@app.get("/access_points", response_class=HTMLResponse)
async def get_access_points():
    query = "SELECT * FROM access_points"
    html_table = create_html_table(query)
    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>Access Points</title>
            </head>
            <body style="text-align: center;">
                <h1>Access Points</h1>
                {html_table}
                <br><br>
                <button onclick="window.location.href='/'">Voltar</button>
            </body>
        </html>
        """
    )

@app.get("/next_wakeups", response_class=HTMLResponse)
async def get_next_wakeups():
    query = f"""
        SELECT *, datetime(datetime, '{timezone}') AS _localtime
        FROM next_wakeups
    """
    html_table = create_html_table(query)
    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>Próximos Acordamentos</title>
            </head>
            <body style="text-align: center;">
                <h1>Próximos Acordamentos</h1>
                {html_table}
                <br><br>
                <button onclick="window.location.href='/'">Voltar</button>
            </body>
        </html>
        """
    )

@app.get("/about", response_class=HTMLResponse)
async def server_about():
    html_content = f"""
    <!DOCTYPE html>
    <html>
        <body style="text-align: center;">
            <p>
                SIMPAT {__version__}
                <br><br>
                <button onclick="window.location.href='/'">Voltar</button>
            </p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/alert")
async def post_alert(alert: Alert):
    next_wakeup = random.randint(min_next_wakeup, max_next_wakeup)

    with sqlite3.connect(db_path, timeout=timeout_s) as con:
        cur = con.cursor()

        cur.execute("""
            INSERT INTO alerts
            (item_id,
             status,
             battery,
             boot_count,
             rep_wakeups,
             bssid)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (alert.item_id,
             alert.status,
             alert.battery,
             alert.boot_count,
             alert.rep_wakeups,
             alert.bssid)
        )
        cur.execute("""
            INSERT INTO next_wakeups (item_id, datetime)
            VALUES (?, datetime('now', ?))
            ON CONFLICT(item_id) DO UPDATE SET
                datetime = excluded.datetime;
            """,
            (alert.item_id,
             f"{next_wakeup} seconds")
        )
        con.commit()

    return {"next_wakeup": next_wakeup}

@app.post("/register_item")
async def post_register_item(item: Annotated[Item, Form()]):
    if item.room.strip() == "":
        raise HTTPException(
            detail="Room is empty",
            status_code=422
        )

    with sqlite3.connect(db_path, timeout=timeout_s) as con:
        cur = con.cursor()

        try:
            cur.execute("""
                INSERT INTO items
                (id,
                 room,
                 description)
                VALUES (?, ?, ?)
                """,
                (item.id,
                 item.room,
                 item.description)
            )
        except sqlite3.IntegrityError:
            # TODO: show error in page
            raise HTTPException(
                detail="ID already exists",
                status_code=422
            )

        con.commit()

    # TODO: show success msg
    return RedirectResponse(url="/", status_code=303)

@app.post("/register_access_point")
async def post_register_access_point(ap: Annotated[AccessPoint, Form()]):
    if ap.bssid.strip() == "":
        raise HTTPException(
            detail="SSID is empty",
            status_code=422
        )
    if ap.description.strip() == "":
        raise HTTPException(
            detail="Description is empty",
            status_code=422
        )

    with sqlite3.connect(db_path, timeout=timeout_s) as con:
        cur = con.cursor()

        try:
            cur.execute("""
                INSERT INTO access_points
                (bssid,
                 description)
                VALUES (?, ?)
                """,
                (ap.bssid,
                 ap.description)
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                detail="AP already exists",
                status_code=422
            )

        con.commit()

    return RedirectResponse(url="/", status_code=303)

@app.post("/update")
async def post_update(item: Annotated[Item, Form()]):
    if item.room.strip() == "":
        raise HTTPException(
            detail="Room is empty",
            status_code=422
        )

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute("""
            UPDATE items
            SET room = ?,
                description = ?
            WHERE id = ?
            """,
            (item.room,
             item.description,
             item.id)
        )
        if cur.rowcount == 0:
            raise HTTPException(
                detail="Item not found",
                status_code=404
            )

    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",  # open
        port=8000,
        reload=True,
    )
