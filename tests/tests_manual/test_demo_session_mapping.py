import sqlite3

db = sqlite3.connect("data/dogfood.db")

print(
    db.execute(
        """
        SELECT
            sessions.id,
            users.id,
            users.name,
            users.email,
            users.role
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.id IN ('jdg_a_91bc', 'jdg_b_44de')
        """
    ).fetchall()
)

db.close()