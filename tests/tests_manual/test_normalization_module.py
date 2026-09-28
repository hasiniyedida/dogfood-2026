import sys
sys.path.insert(0, "src")

import sqlite3

from normalization import calculate_normalized_scores


db = sqlite3.connect("data/dogfood.db")

results = calculate_normalized_scores(db)

print("Number of projects:", len(results))

first_project = results["prj_01"]

print("prj_01 result:")
print(first_project)

db.close()