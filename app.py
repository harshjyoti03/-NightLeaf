from flask import Flask, render_template, request
import sqlite3
import math

app = Flask(__name__)
DB = "database.db"
PER_PAGE = 50

def query(sql, args=(), one=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall()
    conn.close()
    return (rows[0] if rows else None) if one else rows

@app.route("/")
def home():
    page = int(request.args.get("page", 1))
    offset = (page - 1) * PER_PAGE

    manga = query(
        "SELECT id, title, image FROM manga ORDER BY title LIMIT ? OFFSET ?",
        (PER_PAGE, offset)
    )

    total = query("SELECT COUNT(*) AS c FROM manga", one=True)["c"]
    total_pages = math.ceil(total / PER_PAGE)

    return render_template(
        "index.html",
        manga=manga,
        page=page,
        total_pages=total_pages
    )

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    page = int(request.args.get("page", 1))
    offset = (page - 1) * PER_PAGE

    manga = []
    total_pages = 0

    if q:
        manga = query(
            """
            SELECT id, title, image
            FROM manga
            WHERE title LIKE ?
            ORDER BY title
            LIMIT ? OFFSET ?
            """,
            (f"%{q}%", PER_PAGE, offset)
        )

        total = query(
            "SELECT COUNT(*) AS c FROM manga WHERE title LIKE ?",
            (f"%{q}%",),
            one=True
        )["c"]

        total_pages = math.ceil(total / PER_PAGE)

    return render_template(
        "search.html",
        manga=manga,
        q=q,
        page=page,
        total_pages=total_pages
    )

@app.route("/manga/<int:manga_id>")
def manga_detail(manga_id):
    manga = query("SELECT * FROM manga WHERE id=?", (manga_id,), one=True)
    return render_template("manga.html", manga=manga)

if __name__ == "__main__":
    app.run(debug=True)
