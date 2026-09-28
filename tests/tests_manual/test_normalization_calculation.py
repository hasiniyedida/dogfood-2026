import sqlite3
import math
from collections import defaultdict

db = sqlite3.connect("data/dogfood.db")

# --------------------------------------------------
# 1. Get every completed review as ONE numerical score
# --------------------------------------------------

rows = db.execute(
    """
    SELECT
        scores.id,
        scores.judge_id,
        scores.project_id,
        scores.functionality,
        scores.quality,
        score_values.criterion_id,
        score_values.value,
        rubric_criteria.weight
    FROM scores
    LEFT JOIN score_values
        ON scores.id = score_values.score_id
    LEFT JOIN rubric_criteria
        ON score_values.criterion_id = rubric_criteria.id
    ORDER BY scores.id, score_values.criterion_id
    """
).fetchall()

reviews = {}

for row in rows:
    (
        score_id,
        judge_id,
        project_id,
        functionality,
        quality,
        criterion_id,
        value,
        weight,
    ) = row

    if score_id not in reviews:
        reviews[score_id] = {
            "judge_id": judge_id,
            "project_id": project_id,
            "values": [],
            "functionality": functionality,
            "quality": quality,
        }

    if criterion_id is not None:
        reviews[score_id]["values"].append((value, weight))


# --------------------------------------------------
# 2. Turn each review into ONE score
# --------------------------------------------------

for review in reviews.values():

    if review["values"]:
        total_weight = sum(weight for value, weight in review["values"])

        if total_weight > 0:
            review["score"] = sum(
                value * weight
                for value, weight in review["values"]
            ) / total_weight
        else:
            review["score"] = None

    elif (
        review["functionality"] is not None
        and review["quality"] is not None
    ):
        # Fixture scores have no weights specified,
        # so use their simple mean.
        review["score"] = (
            review["functionality"]
            + review["quality"]
        ) / 2.0

    else:
        review["score"] = None


# --------------------------------------------------
# 3. Group reviews by judge
# --------------------------------------------------

judge_reviews = defaultdict(list)

for review in reviews.values():
    if review["score"] is not None:
        judge_reviews[review["judge_id"]].append(review)


# --------------------------------------------------
# 4. Calculate each judge's mean and standard deviation
# --------------------------------------------------

judge_stats = {}

for judge_id, judge_review_list in judge_reviews.items():

    values = [
        review["score"]
        for review in judge_review_list
    ]

    mean = sum(values) / len(values)

    variance = sum(
        (value - mean) ** 2
        for value in values
    ) / len(values)

    standard_deviation = math.sqrt(variance)

    judge_stats[judge_id] = {
        "mean": mean,
        "sd": standard_deviation,
        "count": len(values),
    }


# --------------------------------------------------
# 5. Convert each review to a normalized z-score
# --------------------------------------------------

for review in reviews.values():

    if review["score"] is None:
        continue

    stats = judge_stats[review["judge_id"]]

    if stats["sd"] > 0:
        review["z_score"] = (
            review["score"] - stats["mean"]
        ) / stats["sd"]
    else:
        # A judge who gives every review the same score
        # has no measurable spread.
        review["z_score"] = 0.0


# --------------------------------------------------
# 6. Aggregate normalized scores by project
# --------------------------------------------------

project_scores = defaultdict(list)

for review in reviews.values():

    if "z_score" in review:
        project_scores[review["project_id"]].append(
            review["z_score"]
        )


# --------------------------------------------------
# 7. Print judge statistics
# --------------------------------------------------

print("JUDGE NORMALIZATION STATS")
print("=" * 60)

for judge_id, stats in sorted(judge_stats.items()):

    print(
        f"Judge {judge_id} | "
        f"Reviews: {stats['count']} | "
        f"Mean: {stats['mean']:.3f} | "
        f"SD: {stats['sd']:.3f}"
    )


# --------------------------------------------------
# 8. Print normalized project scores
# --------------------------------------------------

print("\nPROJECT NORMALIZED SCORES")
print("=" * 60)

for project_id in sorted(project_scores):

    values = project_scores[project_id]

    average_z = sum(values) / len(values)

    print(
        f"Project: {project_id} | "
        f"Reviews: {len(values)} | "
        f"Average z-score: {average_z:.3f}"
    )


db.close()