import sqlite3

db = sqlite3.connect("data/dogfood.db")

total_scores = db.execute(
    """
    SELECT COUNT(*)
    FROM scores
    """
).fetchone()[0]

new_scores = db.execute(
    """
    SELECT COUNT(DISTINCT score_id)
    FROM score_values
    """
).fetchone()[0]

print("Total score records:", total_scores)
print("Scores with new criterion values:", new_scores)
print("Scores still relying on old fields:", total_scores - new_scores)

db.close()