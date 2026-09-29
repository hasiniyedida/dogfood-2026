# Architecture

Dogfood 2026 Portal is a self-hostable Flask application backed by SQLite and packaged with Docker Compose.

The design prioritizes local operation, explicit backend authorization, a relational data model, and seeded fixture data so that the portal can be evaluated without external services.

## System overview

```text id="f3xq6k"
Browser
   │
   ▼
Flask application
   │
   ├── Authentication / sessions
   ├── Role authorization
   ├── Participant workflows
   ├── Judge workflows
   ├── Organizer workflows
   ├── Public gallery
   └── Community voting / comments
   │
   ▼
SQLite database
   │
   ├── Portal data
   ├── Judging data
   └── T3 community data
```

The application listens on port `8080`.

## Runtime

The project is packaged with Docker Compose.

`docker compose up`:

1. Builds the application image when required.
2. Starts the Flask application.
3. Initializes the SQLite schema.
4. Seeds the supplied fixture data and demo sessions.
5. Serves the portal on `http://localhost:8080`.

The SQLite database is stored under the local `data/` directory.

No hosted database, cloud account, external API, or third-party hosted service is required.

## Application structure

### Flask application

`src/app.py` contains the HTTP routes and the server-rendered portal pages.

The application exposes:

* Public gallery and event pages
* Authentication and session handling
* Participant project workflows
* Judge scoring workflows
* Organizer judging dashboards
* Admin workspace
* Community voting
* Project comments
* CSV export
* Normalized judging results

### Database layer

`src/db.py` provides SQLite connections and database initialization.

`src/schema.sql` defines the relational schema.

The schema separates core event data, teams, projects, judging data, authentication sessions, and T3 community data.

### Seed data

`src/seed.py` loads the supplied fixture data and creates the local demo environment.

The seed process includes:

* Event data
* Tracks
* Teams
* Team membership
* Projects
* Judges and scores
* Judge assignments derived from the fixture score records
* Demo sessions
* Participant demo membership

## Authorization model

Authentication is session-based.

The application identifies the current user from the session cookie and performs role checks on protected routes.

Backend authorization is used rather than relying on frontend visibility.

For judging, the backend verifies that:

* A request is authenticated as a judge.
* A judge is assigned to the requested project before accepting a score.
* Judges cannot retrieve peer judges' scores.
* Participants cannot retrieve judge scores.
* Organizer-only endpoints require the organizer role.

This role isolation is part of the T2 judging-integrity design.

## Participant workflow

Participants can:

1. Access the participant workspace.
2. Create a project for a team they belong to.
3. Edit a draft project.
4. Submit the project before the event deadline.

The backend checks team membership, track validity, project state, and the submission deadline.

Submitted projects are exposed through the public gallery.

## Judging workflow

The judging system uses configurable rubric criteria and weighted scores.

Judges receive assignments to specific projects and submit scores through protected backend endpoints.

The organizer dashboard exposes judging progress and normalized results.

Normalization is implemented in `src/normalization.py` and documented separately in `JUDGING.md`.

## Community voting

T3 community voting uses organizer-issued, event-scoped voter tokens.

The voting flow is:

```text id="7x5m3p"
Organizer
   │
   └── issues voter token
             │
             ▼
       Community ballot
             │
             ├── randomized project order
             └── one vote per token
                     │
                     ▼
              Community vote
                     │
                     └── audit log
```

Community comments use the same voter-token model.

The backend enforces:

* Voting-window boundaries
* Event-scoped voter tokens
* One vote per voter token
* Project/event relationship validation
* Comment rate limiting
* Audit logging
* Hidden community results while voting is active

The database also enforces the one-vote constraint through a uniqueness constraint on `(event_id, voter_token_id)`.

## Public gallery

The gallery exposes submitted projects without requiring authentication.

Projects can be searched and filtered by track.

Community voting is connected to the public event/project experience rather than being implemented as an isolated feature.

## Design decisions

### SQLite

SQLite keeps the application self-contained and suitable for the hackathon's offline, single-command local deployment requirement.

### Backend role enforcement

Authorization is enforced at the backend rather than only hiding controls in the frontend. This prevents users from bypassing role restrictions by directly calling protected endpoints.

### Relational schema

Separate tables are used for teams, memberships, projects, assignments, scores, voter tokens, votes, comments, and audit records. Foreign keys and uniqueness constraints encode important integrity rules in the database.

### Seeded fixture data

The supplied fixture data is loaded into the local database so that the portal starts with realistic teams, projects, judges, and scores rather than an empty application.

### Separate normalization module

Judging normalization is isolated in `src/normalization.py` so that the calculation can be reasoned about and documented independently from the HTTP routes.

## Documentation map

* `README.md` — setup, features, demo accounts, and evaluation notes
* `DATA-MODEL.md` — relational data model
* `JUDGING.md` — scoring and normalization methodology
* `.dogfood.toml` — acceptance-checker configuration and claimed tiers
* `src/schema.sql` — database schema
* `src/seed.py` — fixture and demo-data initialization
