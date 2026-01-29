import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS liked_manga (
    manga_id INTEGER PRIMARY KEY
)
""")

conn.commit()
conn.close()

print("liked_manga table ready")
