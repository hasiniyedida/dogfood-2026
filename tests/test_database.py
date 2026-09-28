import sqlite3

db = sqlite3.connect("data/dogfood.db")

print("Events:")
print(db.execute(
    "SELECT id, name FROM events"
).fetchall())

print("Tracks:")
print(db.execute(
    "SELECT id, name, event_id FROM tracks"
).fetchall())

print("Projects:")
print(db.execute(
    "SELECT COUNT(*) FROM projects"
).fetchone())

print("Scores:")
print(db.execute(
    "SELECT COUNT(*) FROM scores"
).fetchone())

print("Sessions:")
print(db.execute(
    "SELECT COUNT(*) FROM sessions"
).fetchone())

db.close()