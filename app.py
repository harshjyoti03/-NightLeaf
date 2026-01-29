from flask import Flask, render_template, request
import sqlite3
import math

from flask import redirect, url_for

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


# 🌿 LANDING PAGE
@app.route("/")
def landing():
    return render_template("landing.html")


# 📚 EXPLORE PAGE
@app.route("/explore")
@app.route("/explore")
def explore():
    manga = query("SELECT id, title, image FROM manga ORDER BY RANDOM() LIMIT 60")

    liked_rows = query("SELECT manga_id FROM liked_manga")
    liked_ids = {row["manga_id"] for row in liked_rows}

    return render_template(
        "index.html",
        manga=manga,
        liked_ids=liked_ids
    )



# 🔍 BASIC SEARCH
@app.route("/search")
def search():
    q = request.args.get("q", "").strip()

    statuses = request.args.getlist("status")
    genres = request.args.getlist("genre")

    year_from = request.args.get("year_from")
    year_to = request.args.get("year_to")

    sort = request.args.get("sort", "az")

    show_results = bool(q or statuses or genres or year_from or year_to)

    manga = []

    if show_results:
        sql = "SELECT id, title, image, year FROM manga WHERE 1=1"
        params = []

        if q:
            sql += " AND title LIKE ?"
            params.append(f"%{q}%")

        if statuses:
            sql += " AND (" + " OR ".join(["status = ?"] * len(statuses)) + ")"
            params.extend([s.upper() for s in statuses])

        if genres:
            sql += " AND (" + " OR ".join(["genres LIKE ?"] * len(genres)) + ")"
            params.extend([f"%{g}%" for g in genres])

        if year_from:
            sql += " AND year >= ?"
            params.append(year_from)

        if year_to:
            sql += " AND year <= ?"
            params.append(year_to)

        if sort == "az":
            sql += " ORDER BY title ASC"
        elif sort == "za":
            sql += " ORDER BY title DESC"
        elif sort == "oldest":
            sql += " ORDER BY year ASC"
        elif sort == "latest":
            sql += " ORDER BY year DESC"

        manga = query(sql, params)

    liked_rows = query("SELECT manga_id FROM liked_manga")
    liked_ids = {row["manga_id"] for row in liked_rows}

    return render_template(
        "search.html",
        manga=manga,
        liked_ids=liked_ids,
        q=q,
        statuses=statuses,
        genres=genres,
        year_from=year_from,
        year_to=year_to,
        sort=sort,
        show_results=show_results
    )


# 📂 MANGA DIRECTORY (NEW)
@app.route("/directory")
def directory():
    letter = request.args.get("letter", "")

    if letter:
        if letter == "#":
            manga = query(
                "SELECT id, title FROM manga WHERE title GLOB '[0-9]*' ORDER BY title"
            )
        else:
            manga = query(
                "SELECT id, title FROM manga WHERE title LIKE ? ORDER BY title",
                (f"{letter}%",)
            )
    else:
        manga = query("SELECT id, title FROM manga ORDER BY title")

    return render_template(
        "directory.html",
        manga=manga,
        letter=letter
    )

# 📖 MANGA DETAIL
@app.route("/manga/<int:manga_id>")
def manga_detail(manga_id):
    manga = query(
        "SELECT * FROM manga WHERE id = ?",
        (manga_id,),
        one=True
    )

    liked_rows = query("SELECT manga_id FROM liked_manga")
    liked_ids = {row["manga_id"] for row in liked_rows}

    return render_template(
        "manga.html",
        manga=manga,
        liked_ids=liked_ids
    )


@app.route("/like/<int:manga_id>", methods=["POST"])
def like_toggle(manga_id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM liked_manga WHERE manga_id = ?", (manga_id,))
    exists = cur.fetchone()

    if exists:
        cur.execute("DELETE FROM liked_manga WHERE manga_id = ?", (manga_id,))
    else:
        cur.execute("INSERT INTO liked_manga (manga_id) VALUES (?)", (manga_id,))

    conn.commit()
    conn.close()

    # 🔥 Redirect DIRECTLY to manga page (no referrer)
    return redirect(url_for("manga_detail", manga_id=manga_id))


@app.route("/collection")
def collection():
    manga = query("""
        SELECT m.id, m.title, m.image
        FROM manga m
        JOIN liked_manga l ON m.id = l.manga_id
        ORDER BY m.title
    """)

    return render_template("collection.html", manga=manga)


# 🚫 CUSTOM 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
