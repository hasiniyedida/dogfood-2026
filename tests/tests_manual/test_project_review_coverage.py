import sqlite3

db = sqlite3.connect("data/dogfood.db")

rows = db.execute(
    """
    SELECT
        projects.id,
        projects.title,
        COUNT(DISTINCT scores.judge_id) AS judge_count,
        COUNT(scores.id) AS score_count,
        AVG(
            CASE
                WHEN score_values.value IS NOT NULL
                THEN score_values.value
                ELSE (scores.functionality + scores.quality) / 2.0
            END
        ) AS average_raw_score
    FROM projects
    LEFT JOIN scores
        ON projects.id = scores.project_id
    LEFT JOIN score_values
        ON scores.id = score_values.score_id
    GROUP BY projects.id, projects.title
    ORDER BY projects.id
    """
).fetchall()

for row in rows:
    print(
        f"Project: {row[0]} | "
        f"Title: {row[1]} | "
        f"Judges: {row[2]} | "
        f"Scores: {row[3]} | "
        f"Average: {row[4]:.2f}" if row[4] is not None
        else
        f"Project: {row[0]} | "
        f"Title: {row[1]} | "
        f"Judges: {row[2]} | "
        f"Scores: {row[3]} | "
        f"Average: N/A"
    )

db.close()