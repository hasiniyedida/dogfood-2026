import math
from collections import defaultdict


def calculate_normalized_scores(db):
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
            reviews[score_id]["values"].append(
                (value, weight)
            )

    for review in reviews.values():

        if review["values"]:
            total_weight = sum(
                weight
                for value, weight in review["values"]
            )

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
            review["score"] = (
                review["functionality"]
                + review["quality"]
            ) / 2.0

        else:
            review["score"] = None

    judge_reviews = defaultdict(list)

    for review in reviews.values():
        if review["score"] is not None:
            judge_reviews[review["judge_id"]].append(review)

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

    project_scores = defaultdict(list)

    for review in reviews.values():

        if review["score"] is None:
            continue

        stats = judge_stats[review["judge_id"]]

        if stats["sd"] > 0:
            z_score = (
                review["score"] - stats["mean"]
            ) / stats["sd"]
        else:
            z_score = 0.0

        project_scores[review["project_id"]].append(
            z_score
        )

        project_reviews = defaultdict(list)

        for review in reviews.values():

            if review["score"] is not None:
                project_reviews[review["project_id"]].append(
                    review["score"]
                )

    results = {}

    for project_id, values in project_scores.items():

        raw_values = project_reviews[project_id]

        results[project_id] = {
            "review_count": len(values),
            "raw_average": (
                sum(raw_values) / len(raw_values)
            ),
            "normalized_score": (
                sum(values) / len(values)
            ),
        }

    return results
