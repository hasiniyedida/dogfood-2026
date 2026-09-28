import sqlite3
import math

db = sqlite3.connect("data/dogfood.db")

rows = db.execute(
    """
    SELECT
        users.name,
        CASE
            WHEN score_values.value IS NOT NULL
            THEN score_values.value
            ELSE (scores.functionality + scores.quality) / 2.0
        END AS score
    FROM users
    JOIN scores
        ON users.id = scores.judge_id
    LEFT JOIN score_values
        ON scores.id = score_values.score_id
    WHERE users.role = 'judge'
    ORDER BY users.name, scores.id
    """
).fetchall()

judge_scores = {}

for name, score in rows:
    judge_scores.setdefault(name, []).append(score)

for name, scores in judge_scores.items():
    mean = sum(scores) / len(scores)

    variance = sum(
        (score - mean) ** 2
        for score in scores
    ) / len(scores)

    standard_deviation = math.sqrt(variance)

    print(
        f"Judge: {name} | "
        f"N: {len(scores)} | "
        f"Mean: {mean:.2f} | "
        f"SD: {standard_deviation:.2f}"
    )

db.close()