import requests
import sqlite3
import time
import re

DB = "database.db"
API_URL = "https://graphql.anilist.co"

QUERY = """
query ($page: Int) {
  Page(page: $page, perPage: 50) {
    media(type: MANGA) {
      id
      title { romaji english }
      description
      genres
      status
      startDate { year }
      coverImage { large }
      staff {
        edges {
          role
          node {
            name { full }
          }
        }
      }
    }
  }
}
"""

def clean_html(text):
    if not text:
        return ""
    return re.sub("<.*?>", "", text)

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS manga (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        authors TEXT,
        genres TEXT,
        status TEXT,
        year INTEGER,
        image TEXT
    )
    """)
    conn.commit()
    conn.close()

def import_manga(pages=200):  # 200 × 50 = 10,000
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    for page in range(1, pages + 1):
        print(f"Fetching page {page}")
        res = requests.post(
            API_URL,
            json={"query": QUERY, "variables": {"page": page}},
            headers={"Content-Type": "application/json"}
        )

        data = res.json()["data"]["Page"]["media"]

        for m in data:
            title = m["title"]["english"] or m["title"]["romaji"]
            description = clean_html(m["description"])
            genres = ", ".join(m["genres"])
            status = m["status"]
            year = m["startDate"]["year"]
            image = m["coverImage"]["large"]

            authors = []
            for s in m["staff"]["edges"]:
                if s["role"] in ("Story", "Art", "Original Creator"):
                    authors.append(s["node"]["name"]["full"])

            cur.execute("""
            INSERT OR IGNORE INTO manga
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m["id"],
                title,
                description,
                ", ".join(authors),
                genres,
                status,
                year,
                image
            ))

        conn.commit()
        time.sleep(1)

    conn.close()
    print("✅ Manga import completed")

if __name__ == "__main__":
    init_db()
    import_manga()
