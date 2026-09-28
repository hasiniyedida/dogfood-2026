import sqlite3

db = sqlite3.connect("data/dogfood.db")

print("RUBRIC:")
rows = db.execute(
    """
    SELECT id, event_id, name, weight
    FROM rubric_criteria
    ORDER BY id
    """
).fetchall()

for row in rows:
    print(row)

print("\nSCORE WITH CRITERION VALUES:")
rows = db.execute(
    """
    SELECT
        scores.id,
        scores.judge_id,
        scores.project_id,
        score_values.criterion_id,
        score_values.value
    FROM scores
    JOIN score_values
        ON scores.id = score_values.score_id
    ORDER BY scores.id, score_values.criterion_id
    LIMIT 10
    """
).fetchall()

for row in rows:
    print(row)

print("\nLEGACY FIXTURE SCORES:")
rows = db.execute(
    """
    SELECT
        id,
        judge_id,
        project_id,
        functionality,
        quality
    FROM scores
    WHERE functionality IS NOT NULL
    AND quality IS NOT NULL
    LIMIT 10
    """
).fetchall()

for row in rows:
    print(row)

db.close()