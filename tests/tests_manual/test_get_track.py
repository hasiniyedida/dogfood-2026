import sqlite3

db = sqlite3.connect("data/dogfood.db")

rows = db.execute(
    """
    SELECT id, name, event_id
    FROM tracks
    WHERE event_id = ?
    """,
    ("5feb1fba-aec9-4473-bdf4-0a347b450878",)
).fetchall()

print(rows)

db.close()