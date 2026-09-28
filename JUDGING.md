# Judging Methodology

## Overview

The judging system stores each completed review against a specific judge and project. Each review produces a numerical raw score and may include a written comment.

The portal supports configurable rubric criteria. When criterion-level scores are available, the review's raw score is calculated using the configured criterion weights.

For fixture data that uses the provided `functionality` and `quality` fields without configured rubric weights, the portal calculates the raw score as the simple mean of those two values.

The normalization method described below is an implementation choice for this submission. The Dogfood specification requires normalization to be documented and defensible, but does not prescribe a specific normalization formula.

## Raw Score Calculation

### Configurable rubric reviews

For a review containing criterion-level scores:

1. Each criterion has a configured weight.

2. The weighted raw score is calculated as:

   `raw score = sum(score × weight) / sum(weights)`

3. Only criterion values stored for that review are included.

### Fixture/legacy reviews

The supplied fixture contains `functionality` and `quality` values but does not specify rubric weights.

For those reviews, the portal uses:

`raw score = (functionality + quality) / 2`

This avoids inventing rubric weights for the supplied fixture data.

## Cross-Judge Normalization

Judges may use scoring scales differently. To reduce the effect of different judge scoring tendencies, the portal performs judge-specific z-score normalization.

For each judge:

1. Collect the raw scores from that judge's completed reviews.

2. Calculate the judge's mean raw score.

3. Calculate the population standard deviation of those scores.

4. For each review, calculate:

   `z = (raw score - judge mean) / judge standard deviation`

5. If a judge's standard deviation is zero, the normalized score for that judge's reviews is set to `0.0`. This prevents division by zero when the judge has given identical scores.

## Project Normalized Score

Each project's normalized score is the arithmetic mean of the normalized scores contributed by its completed reviews:

`project normalized score = mean(review z-scores)`

The organizer results endpoint also preserves:

* review count
* raw average
* normalized score

This allows organizers to see both the original scoring level and the normalized result.

## Limitations

### Small review counts

The supplied fixture contains projects with different numbers of assigned and completed reviews. Some judges also have relatively few completed reviews.

A judge mean and standard deviation estimated from a small number of reviews can be unstable. Consequently, a normalized score based on a judge with very few reviews should not be interpreted as equally statistically reliable as one based on a large review set.

### Zero standard deviation

If all of a judge's completed reviews have the same raw score, the standard deviation is zero and a conventional z-score cannot be calculated. The implementation assigns a normalized value of `0.0` for those reviews instead of dividing by zero.

### Uneven review coverage

Projects do not necessarily have the same number of completed reviews. The project normalized score is therefore based on the reviews that are actually completed rather than assuming a fixed number of reviews per project.

### Normalization does not replace raw scores

Normalization is provided to reduce differences in judge scoring behavior. The portal retains raw averages and review counts so organizers can inspect the underlying results rather than relying exclusively on the normalized value.

## Transparency

The normalization method is implemented in `src/normalization.py`.

The organizer can access normalized results through:

`GET /api/organizer/normalized-results`

The organizer judging-progress page displays the project review count, raw average, and normalized score together.
