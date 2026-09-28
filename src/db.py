import sqlite3

DB_PATH = "data/dogfood.db"


def get_db():
    return sqlite3.connect(DB_PATH)


def init_db():
    db = get_db()

    with open("src/schema.sql", "r") as file:
        db.executescript(file.read())

    db.commit()
    db.close()