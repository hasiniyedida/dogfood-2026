import sqlite3

db = sqlite3.connect("data/dogfood.db")

print("OLD SCORE ROW:")
print(
    db.execute(
        """
        SELECT
            id,
            judge_id,
            project_id,
            functionality,
            quality,
            comment
        FROM scores
        WHERE project_id = 'prj_01'
        AND judge_id = 8
        """
    ).fetchall()
)

print("\nNEW SCORE VALUES:")
print(
    db.execute(
        """
        SELECT
            score_values.score_id,
            rubric_criteria.name,
            score_values.value
        FROM score_values
        JOIN rubric_criteria
            ON score_values.criterion_id = rubric_criteria.id
        WHERE score_values.score_id = 1
        """
    ).fetchall()
)

db.close()