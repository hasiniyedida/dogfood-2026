import sqlite3

db = sqlite3.connect("data/dogfood.db")

tables = db.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name = 'score_values'
    """
).fetchall()

print("score_values table:", tables)

columns = db.execute(
    """
    PRAGMA table_info(score_values)
    """
).fetchall()

print("columns:")
for column in columns:
    print(column)

db.close()