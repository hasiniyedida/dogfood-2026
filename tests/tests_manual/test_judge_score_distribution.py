import sqlite3

db = sqlite3.connect("data/dogfood.db")

rows = db.execute(
    """
    SELECT
        users.name,
        COUNT(scores.id) AS score_count,
        AVG(
            CASE
                WHEN score_values.value IS NOT NULL
                THEN score_values.value
                ELSE (scores.functionality + scores.quality) / 2.0
            END
        ) AS average_score
    FROM users
    JOIN scores
        ON users.id = scores.judge_id
    LEFT JOIN score_values
        ON scores.id = score_values.score_id
    WHERE users.role = 'judge'
    GROUP BY users.id
    ORDER BY users.name
    """
).fetchall()

for row in rows:
    print(
        f"Judge: {row[0]} | "
        f"Scores: {row[1]} | "
        f"Average: {row[2]:.2f}"
    )

db.close()