# Dogfood 2026 Portal

A self-hostable hackathon registration, submission, judging, community voting, and results portal built for Dogfood 2026.

## What it provides

### T1 Core
- Session-based authentication
- Participant, judge, organizer, and admin roles
- Event and track data
- Team membership
- Project creation and editing
- Submission deadline enforcement
- Public project gallery with search and track filtering

### T2 Judging
- Judge assignments
- Configurable weighted rubric
- Backend-enforced judge role isolation
- Organizer judging-progress dashboard
- Cross-judge score normalization
- CSV export
- Documented normalization methodology

### Community voting
- Organizer-issued voter tokens
- One vote per voter token
- Randomized project ordering on ballots
- Project comments
- Comment rate limiting
- Duplicate-vote prevention
- Audit trail for community actions
- Results hidden while voting is active

## Running locally

Requirements:

- Docker
- Docker Compose

Start the portal with:

    docker compose up

The application is available at:

    http://localhost:8080

The database is SQLite and is stored locally under `data/`.

No cloud account, hosted database, external API, or third-party hosted service is required.

## Demo accounts

The seeded demo sessions use these cookies:

| Role | Session |
|---|---|
| Organizer | `org_7f2a` |
| Judge A | `jdg_a_91bc` |
| Judge B | `jdg_b_44de` |
| Participant | `prt_2e88` |
| Admin | `adm_3c91` |

The corresponding demo login emails are:

- `organizer@example.org`
- `marek.nowak@example.org`
- `priya.nair@example.org`
- `participant@example.org`
- `admin@example.org`

The judge demo accounts are derived from judges that have scores in the supplied fixture data.

## Judging and normalization

The portal uses configurable rubric criteria and weighted raw scores for criterion-level reviews.

Cross-judge normalization uses judge-specific population z-scores. The method, formulas, limitations, and zero-standard-deviation handling are documented in `JUDGING.md`.

Implementation:

    src/normalization.py

Organizer normalized results:

    GET /api/organizer/normalized-results

## T3 anti-abuse design

Community voting uses an event-scoped voter token.

A voter token can cast at most one community vote for an event. Duplicate attempts are rejected by both application logic and the database uniqueness constraint.

Community comments are rate-limited to five comments per voter token within ten minutes.

Community vote and comment actions are written to `audit_log`.

Ballots use randomized project ordering with SQL `ORDER BY RANDOM()`.

Community results are unavailable until the voting window has ended.

## Fixture data

The supplied `fixtures.json` is used to seed the demonstration event, teams, judges, projects, and scores.

The fixture dataset is intentionally preserved, including uneven review coverage and other awkward cases supplied by the challenge.

## Acceptance verification

Run:

    python run.py .dogfood.toml

The acceptance checker verifies the required T1 and T2 behaviors, including:

- public gallery access
- fixture project visibility
- closed-event submission rejection
- judge access to own scores
- peer-score isolation
- participant score isolation
- organizer CSV export

Passing the acceptance checker does not by itself establish every tier feature; additional functionality is verified separately.

## Project documentation

- `JUDGING.md` — normalization methodology and limitations
- `ARCHITECTURE.md` — system architecture
- `DATA-MODEL.md` — database structure
- `spec.md` — challenge specification used for implementation

## License

MIT License. See `LICENSE`.