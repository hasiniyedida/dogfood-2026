# Data Model

The portal uses SQLite as its local relational database.

## Core entities

### Users

Stores portal users and their roles.

Important fields:

* `id`
* `name`
* `email`
* `role`

Supported roles include participant, judge, organizer, and admin.

### Events

Stores hackathon event configuration.

Important fields:

* `id`
* `name`
* `submissions_open`
* `submissions_close`

### Tracks

Stores event tracks used to categorize projects.

### Prizes

Stores prizes associated with events.

### Teams

Stores teams belonging to an event.

Important fields:

* `id`
* `name`
* `event_id`

### Team members

Connects users to teams through a composite relationship between `team_id` and `user_id`.

### Team invites

Stores invitations for users to join teams.

Important fields:

* `id`
* `team_id`
* `invited_email`
* `created_at`

## Projects

Projects belong to teams and tracks.

Important fields:

* `id`
* `team_id`
* `track_id`
* `title`
* `summary`
* `repo_url`
* `submitted_at`
* `updated_at`
* `status`

Projects support draft and submitted states. Submission is subject to the event submission deadline.

## Judging

### Rubric criteria

Stores the configurable judging criteria for an event.

Important fields:

* `id`
* `event_id`
* `name`
* `weight`

### Judge assignments

Associates judges with projects they are permitted to review.

### Judge invites

Stores invitations for judges.

### Scores

Stores a judge's score for a project.

A unique constraint prevents the same judge from creating multiple score records for the same project.

### Score values

Stores individual rubric criterion values associated with a score.

The application uses these values when calculating normalized judging results.

## Authentication

### Sessions

Stores the session identifier associated with a user.

The portal uses session cookies to identify the current user and backend role checks to enforce authorization.

## Community voting

### Voting windows

Defines when community voting is open for an event.

### Voter tokens

Stores event-scoped tokens used for link/token-based community voting.

### Community votes

Records a voter's selected project.

A database uniqueness constraint on `(event_id, voter_token_id)` prevents a voter token from casting more than one vote for an event.

### Project comments

Stores comments made by voters on projects.

### Audit log

Records community actions such as votes and comments.

Important fields:

* `event_id`
* `action`
* `voter_token_id`
* `project_id`
* `created_at`

## Relationships

At a high level:

```text
Event
 ├── Tracks
 ├── Prizes
 ├── Teams
 │    ├── Team members → Users
 │    ├── Team invites
 │    └── Projects
 │         └── Track
 ├── Rubric criteria
 ├── Voting windows
 └── Voter tokens
       ├── Community votes → Projects
       └── Project comments → Projects

Users
 ├── Sessions
 ├── Judge assignments → Projects
 └── Scores → Projects
       └── Score values → Rubric criteria
```

The schema is implemented in `src/schema.sql`, while fixture loading and demo data initialization are handled by `src/seed.py`.
