import sqlite3

db = sqlite3.connect("data/dogfood.db")

rows = db.execute(
    """
    SELECT
        score_values.score_id,
        score_values.criterion_id,
        rubric_criteria.name,
        score_values.value
    FROM score_values
    JOIN rubric_criteria
        ON score_values.criterion_id = rubric_criteria.id
    JOIN scores
        ON score_values.score_id = scores.id
    WHERE scores.judge_id = (
        SELECT id
        FROM users
        WHERE email = 'marek.nowak@example.org'
    )
    AND scores.project_id = 'prj_01'
    ORDER BY score_values.criterion_id
    """
).fetchall()

for row in rows:
    print(row)

db.close()