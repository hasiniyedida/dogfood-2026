import sqlite3

db = sqlite3.connect("data/dogfood.db")

rows = db.execute(
    """
    SELECT
        projects.id,
        projects.title,
        COUNT(DISTINCT judge_assignments.judge_id) AS assigned_judges
    FROM projects
    LEFT JOIN judge_assignments
        ON projects.id = judge_assignments.project_id
    GROUP BY projects.id, projects.title
    ORDER BY projects.id
    """
).fetchall()

for row in rows:
    print(
        f"Project: {row[0]} | "
        f"Title: {row[1]} | "
        f"Assigned judges: {row[2]}"
    )

db.close()