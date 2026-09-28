import sqlite3

db = sqlite3.connect("data/dogfood.db")

print(
    db.execute(
        """
        SELECT id, email, role
        FROM users
        WHERE role = 'judge'
        LIMIT 3
        """
    ).fetchall()
)

db.close()