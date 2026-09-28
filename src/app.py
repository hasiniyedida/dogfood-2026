from flask import Flask, request, Response
from db import init_db, get_db
from normalization import calculate_normalized_scores
import sqlite3
from seed import seed_users, seed_event, seed_tracks, seed_teams, seed_team_members, seed_projects, seed_scores, seed_assignments, seed_demo_sessions
import uuid
from datetime import datetime, timezone

app = Flask(__name__)
def get_current_user():
    cookie = request.headers.get("Cookie", "")

    if not cookie.startswith("session="):
        return None

    session_id = cookie.split("=", 1)[1]

    db = get_db()

    user = db.execute(
        """
        SELECT users.id, users.name, users.email, users.role
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.id = ?
        """,
        (session_id,)
    ).fetchone()

    db.close()

    return user

def require_role(role):
    user = get_current_user()

    if user is None:
        return None, ("Not authenticated", 401)

    if user[3] != role:
        return None, ("Forbidden", 403)

    return user, None

@app.get("/whoami")
def whoami():
    user = get_current_user()

    if user is None:
        return "Not authenticated", 401

    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "role": user[3]
    }
@app.get("/organizer-test")
def organizer_test():
    user, error = require_role("organizer")

    if error:
        return error

    return f"Hello {user[1]}, you are the organizer."

@app.get("/projects")
def gallery():
    db = get_db()

    search = request.args.get("search", "").strip()
    track_id = request.args.get("track", "").strip()

    query = """
        SELECT
            projects.id,
            projects.title,
            projects.summary,
            projects.repo_url,
            projects.submitted_at,
            projects.track_id,
            tracks.name
        FROM projects
        JOIN tracks ON projects.track_id = tracks.id
        WHERE projects.status = 'submitted'
    """

    params = []

    if search:
        query += """
            AND (
                projects.title LIKE ?
                OR projects.summary LIKE ?
            )
        """

        search_value = f"%{search}%"
        params.extend([search_value, search_value])

    if track_id:
        query += """
            AND projects.track_id = ?
        """
        params.append(track_id)

    query += " ORDER BY projects.id"

    rows = db.execute(query, params).fetchall()

    db.close()

    return {
        "projects": [
            {
                "id": row[0],
                "title": row[1],
                "summary": row[2],
                "repo_url": row[3],
                "submitted_at": row[4],
                "track_id": row[5],
                "track": row[6]
            }
            for row in rows
        ]
    }, 200

@app.post("/projects/new")
def create_project():
    user, error = require_role("participant")

    if error:
        return error

    team_id = request.form.get("team_id")
    track_id = request.form.get("track_id")
    title = request.form.get("title")
    summary = request.form.get("summary")
    repo_url = request.form.get("repo_url")

    if not all([team_id, track_id, title, summary]):
        return "Missing required fields", 400

    db = get_db()

    event = db.execute(
        """
        SELECT events.submissions_open, events.submissions_close
        FROM events
        JOIN teams ON teams.event_id = events.id
        WHERE teams.id = ?
        """,
        (team_id,)
    ).fetchone()

    if event is None:
        db.close()
        return "Event not found", 404

    opening = datetime.fromisoformat(
        event[0].replace("Z", "+00:00")
    )

    deadline = datetime.fromisoformat(
        event[1].replace("Z", "+00:00")
    )

    now = datetime.now(timezone.utc)

    if now < opening:
        db.close()
        return "Submissions are not open", 403

    if now >= deadline:
        db.close()
        return "Submissions are closed", 403

    membership = db.execute(
        """
        SELECT 1
        FROM team_members
        WHERE team_id = ?
        AND user_id = ?
        """,
        (team_id, user[0])
    ).fetchone()

    if membership is None:
        db.close()
        return "You are not a member of this team", 403

    track = db.execute(
        """
        SELECT 1
        FROM tracks
        JOIN teams ON tracks.event_id = teams.event_id
        WHERE tracks.id = ?
        AND teams.id = ?
        """,
        (track_id, team_id)
    ).fetchone()

    if track is None:
        db.close()
        return "Track not found for this team", 404

    project_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    db.execute(
        """
        INSERT INTO projects
        (id, team_id, track_id, title, summary, repo_url,
        submitted_at, updated_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            team_id,
            track_id,
            title,
            summary,
            repo_url,
            None,
            now,
            "draft"
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Draft created",
        "project_id": project_id
    }, 201

@app.put("/projects/<project_id>")
def edit_project(project_id):
    user, error = require_role("participant")

    if error:
        return error

    title = request.form.get("title")
    summary = request.form.get("summary")
    repo_url = request.form.get("repo_url")

    if not all([title, summary]):
        return "Missing required fields", 400

    db = get_db()

    project = db.execute(
        """
        SELECT team_id, status
        FROM projects
        WHERE id = ?
        """,
        (project_id,)
    ).fetchone()

    if project is None:
        db.close()
        return "Project not found", 404

    team_id, status = project

    if status != "draft":
        db.close()
        return "Only draft projects can be edited", 403

    membership = db.execute(
        """
        SELECT 1
        FROM team_members
        WHERE team_id = ?
        AND user_id = ?
        """,
        (team_id, user[0])
    ).fetchone()

    if membership is None:
        db.close()
        return "You are not a member of this team", 403

    event = db.execute(
        """
        SELECT events.submissions_open, events.submissions_close
        FROM events
        JOIN teams ON teams.event_id = events.id
        JOIN projects ON projects.team_id = teams.id
        WHERE projects.id = ?
        """,
        (project_id,)
).fetchone()

    if event is None:
        db.close()
        return "Event not found", 404

    opening = datetime.fromisoformat(
        event[0].replace("Z", "+00:00")
    )

    deadline = datetime.fromisoformat(
        event[1].replace("Z", "+00:00")
    )

    now = datetime.now(timezone.utc)

    if now < opening:
        db.close()
        return "Submissions are not open", 403

    if now >= deadline:
        db.close()
        return "Submissions are closed", 403

    db.execute(
        """
        UPDATE projects
        SET title = ?,
            summary = ?,
            repo_url = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            title,
            summary,
            repo_url,
            datetime.now(timezone.utc).isoformat(),
            project_id
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Project draft updated",
        "project_id": project_id
    }

@app.post("/projects/<project_id>/submit")
def submit_project(project_id):
    user, error = require_role("participant")

    if error:
        return error

    db = get_db()

    project = db.execute(
        """
        SELECT team_id, status
        FROM projects
        WHERE id = ?
        """,
        (project_id,)
    ).fetchone()

    if project is None:
        db.close()
        return "Project not found", 404

    team_id, status = project

    if status != "draft":
        db.close()
        return "Project is already submitted", 403

    membership = db.execute(
        """
        SELECT 1
        FROM team_members
        WHERE team_id = ?
        AND user_id = ?
        """,
        (team_id, user[0])
    ).fetchone()

    if membership is None:
        db.close()
        return "You are not a member of this team", 403

    event = db.execute(
        """
        SELECT events.submissions_open, events.submissions_close
        FROM events
        JOIN teams ON teams.event_id = events.id
        JOIN projects ON projects.team_id = teams.id
        WHERE projects.id = ?
        """,
        (project_id,)
    ).fetchone()

    if event is None:
        db.close()
        return "Event not found", 404

    opening = datetime.fromisoformat(
        event[0].replace("Z", "+00:00")
    )

    deadline = datetime.fromisoformat(
        event[1].replace("Z", "+00:00")
    )

    now = datetime.now(timezone.utc)

    if now < opening:
        db.close()
        return "Submissions are not open", 403

    if now >= deadline:
        db.close()
        return "Submissions are closed", 403

    db.execute(
        """
        UPDATE projects
        SET status = 'submitted',
            submitted_at = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            now.isoformat(),
            now.isoformat(),
            project_id
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Project submitted",
        "project_id": project_id
    }

@app.post("/api/events")
def create_event():
    user, error = require_role("organizer")

    if error:
        return error

    data = request.get_json()

    if data is None:
        return "JSON body required", 400

    name = data.get("name")
    submissions_open = data.get("submissions_open")
    submissions_close = data.get("submissions_close")
    tracks = data.get("tracks", [])
    prizes = data.get("prizes", [])

    if not all([name, submissions_open, submissions_close]):
        return "Missing required event fields", 400

    if not isinstance(tracks, list):
        return "Tracks must be a list", 400

    if not isinstance(prizes, list):
        return "Prizes must be a list", 400

    try:
        opening = datetime.fromisoformat(
            submissions_open.replace("Z", "+00:00")
        )

        closing = datetime.fromisoformat(
            submissions_close.replace("Z", "+00:00")
        )
    except ValueError:
        return "Invalid event date format", 400

    if closing <= opening:
        return "Submission closing time must be after opening time", 400

    event_id = str(uuid.uuid4())

    db = get_db()

    db.execute(
        """
        INSERT INTO events
        (id, name, submissions_open, submissions_close)
        VALUES (?, ?, ?, ?)
        """,
        (
            event_id,
            name,
            submissions_open,
            submissions_close
        )
    )

    for track in tracks:
        if not isinstance(track, dict):
            db.close()
            return "Each track must be an object", 400

        track_name = track.get("name")

        if not track_name:
            db.close()
            return "Each track requires a name", 400

        db.execute(
            """
            INSERT INTO tracks
            (id, event_id, name)
            VALUES (?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                event_id,
                track_name
            )
        )

    for prize in prizes:
        if not isinstance(prize, dict):
            db.close()
            return "Each prize must be an object", 400

        prize_name = prize.get("name")

        if not prize_name:
            db.close()
            return "Each prize requires a name", 400

        db.execute(
            """
            INSERT INTO prizes
            (event_id, name, description)
            VALUES (?, ?, ?)
            """,
            (
                event_id,
                prize_name,
                prize.get("description")
            )
        )

    db.commit()
    db.close()

    return {
        "message": "Event created",
        "event_id": event_id
    }, 201

@app.post("/api/events/<event_id>/teams")
def create_team(event_id):
    user, error = require_role("organizer")

    if error:
        return error

    data = request.get_json()

    if data is None:
        return "JSON body required", 400

    name = data.get("name")

    if not name:
        return "Team name required", 400

    db = get_db()

    event = db.execute(
        "SELECT 1 FROM events WHERE id = ?",
        (event_id,)
    ).fetchone()

    if event is None:
        db.close()
        return "Event not found", 404

    team_id = str(uuid.uuid4())

    db.execute(
        """
        INSERT INTO teams
        (id, name, event_id)
        VALUES (?, ?, ?)
        """,
        (
            team_id,
            name,
            event_id
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Team created",
        "team_id": team_id
    }, 201

@app.post("/api/teams/<team_id>/invites")
def create_team_invite(team_id):
    user, error = require_role("organizer")

    if error:
        return error

    data = request.get_json()

    if not data:
        return "Invalid request", 400

    invited_email = data.get("email")

    if not invited_email:
        return "Email is required", 400

    db = get_db()

    team = db.execute(
        """
        SELECT id
        FROM teams
        WHERE id = ?
        """,
        (team_id,)
    ).fetchone()

    if team is None:
        db.close()
        return "Team not found", 404

    invite_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    db.execute(
        """
        INSERT INTO team_invites
        (id, team_id, invited_email, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            invite_id,
            team_id,
            invited_email,
            created_at
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Invite created",
        "invite_id": invite_id,
        "invite_link": f"/api/team-invites/{invite_id}/accept"
    }, 201

@app.post("/api/team-invites/<invite_id>/accept")
def accept_team_invite(invite_id):
    user, error = require_role("participant")

    if error:
        return error

    db = get_db()

    invite = db.execute(
        """
        SELECT team_id, invited_email
        FROM team_invites
        WHERE id = ?
        """,
        (invite_id,)
    ).fetchone()

    if invite is None:
        db.close()
        return "Invite not found", 404

    team_id = invite[0]
    invited_email = invite[1]

    if user[2] != invited_email:
        db.close()
        return "This invite is not for this participant", 403

    db.execute(
        """
        INSERT OR IGNORE INTO team_members
        (team_id, user_id)
        VALUES (?, ?)
        """,
        (team_id, user[0])
    )

    db.execute(
        """
        DELETE FROM team_invites
        WHERE id = ?
        """,
        (invite_id,)
    )

    db.commit()
    db.close()

    return {
        "message": "Invite accepted",
        "team_id": team_id
    }, 200

@app.get("/api/judge/scores")
def judge_scores():
    user, error = require_role("judge")

    if error:
        return error

    requested_judge = request.args.get("judge")

    if requested_judge is not None:
        return "Forbidden", 403

    db = get_db()

    rows = db.execute(
        """
        SELECT
            scores.project_id,
            scores.comment,
            rubric_criteria.id,
            rubric_criteria.name,
            rubric_criteria.weight,
            score_values.value,
            scores.functionality,
            scores.quality
        FROM scores
        LEFT JOIN score_values
            ON scores.id = score_values.score_id
        LEFT JOIN rubric_criteria
            ON score_values.criterion_id = rubric_criteria.id
        WHERE scores.judge_id = ?
        ORDER BY scores.project_id, rubric_criteria.id
        
        """,
        (user[0],)
    ).fetchall()

    db.close()

    scores = []

    for row in rows:
        if row[2] is not None:
            scores.append(
                {
                    "project_id": row[0],
                    "comment": row[1],
                    "criterion_id": row[2],
                    "criterion": row[3],
                    "weight": row[4],
                    "value": row[5]
                }
            )
        else:
            scores.append(
                {
                    "project_id": row[0],
                    "comment": row[1],
                    "criterion_id": None,
                    "criterion": "Legacy",
                    "weight": None,
                    "value": None,
                    "functionality": row[6],
                    "quality": row[7]
                }
            )

    return {
        "scores": scores
    }

@app.post("/api/events/<event_id>/rubric")
def create_rubric_criterion(event_id):
    user, error = require_role("organizer")

    if error:
        return error

    data = request.get_json()

    if not data:
        return "Invalid request", 400

    name = data.get("name")
    weight = data.get("weight")

    if not name:
        return "Name is required", 400

    if weight is None:
        return "Weight is required", 400

    try:
        weight = float(weight)
    except (TypeError, ValueError):
        return "Weight must be a number", 400

    db = get_db()

    event = db.execute(
        """
        SELECT id
        FROM events
        WHERE id = ?
        """,
        (event_id,)
    ).fetchone()

    if event is None:
        db.close()
        return "Event not found", 404

    criterion_id = db.execute(
        """
        INSERT INTO rubric_criteria
        (event_id, name, weight)
        VALUES (?, ?, ?)
        """,
        (
            event_id,
            name,
            weight
        )
    ).lastrowid

    db.commit()
    db.close()

    return {
        "message": "Rubric criterion created",
        "criterion_id": criterion_id,
        "event_id": event_id,
        "name": name,
        "weight": weight
    }, 201

@app.post("/api/judge/invites")
def create_judge_invite():
    user, error = require_role("organizer")

    if error:
        return error

    data = request.get_json()

    if not data:
        return "Invalid request", 400

    email = data.get("email")

    if not email:
        return "Email is required", 400

    db = get_db()

    judge = db.execute(
        """
        SELECT id
        FROM users
        WHERE email = ? AND role = 'judge'
        """,
        (email,)
    ).fetchone()

    if judge is None:
        db.close()
        return "Judge not found", 404

    invite_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    db.execute(
        """
        INSERT INTO judge_invites
        (id, email, created_at)
        VALUES (?, ?, ?)
        """,
        (
            invite_id,
            email,
            created_at
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Judge invite created",
        "invite_id": invite_id,
        "invite_link": f"/api/judge-invites/{invite_id}/accept"
    }, 201

@app.post("/api/judge-invites/<invite_id>/accept")
def accept_judge_invite(invite_id):
    user, error = require_role("judge")

    if error:
        return error

    db = get_db()

    invite = db.execute(
        """
        SELECT id, email, accepted_at
        FROM judge_invites
        WHERE id = ?
        """,
        (invite_id,)
    ).fetchone()

    if invite is None:
        db.close()
        return "Invite not found", 404

    if invite[2] is not None:
        db.close()
        return "Invite already accepted", 409

    if invite[1] != user[2]:
        db.close()
        return "Invite does not belong to this judge", 403

    accepted_at = datetime.now(timezone.utc).isoformat()

    db.execute(
        """
        UPDATE judge_invites
        SET accepted_at = ?
        WHERE id = ?
        """,
        (
            accepted_at,
            invite_id
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Judge invite accepted",
        "invite_id": invite_id
    }, 200

@app.post("/api/judge/assignments")
def create_judge_assignment():
    user, error = require_role("organizer")

    if error:
        return error

    data = request.get_json()

    if not data:
        return "Invalid request", 400

    judge_id = data.get("judge_id")
    project_id = data.get("project_id")

    if not judge_id or not project_id:
        return "judge_id and project_id are required", 400

    db = get_db()

    judge = db.execute(
        """
        SELECT id
        FROM users
        WHERE id = ? AND role = 'judge'
        """,
        (judge_id,)
    ).fetchone()

    if judge is None:
        db.close()
        return "Judge not found", 404

    project = db.execute(
        """
        SELECT id
        FROM projects
        WHERE id = ?
        """,
        (project_id,)
    ).fetchone()

    if project is None:
        db.close()
        return "Project not found", 404

    try:
        db.execute(
            """
            INSERT INTO judge_assignments
            (judge_id, project_id)
            VALUES (?, ?)
            """,
            (judge_id, project_id)
        )

        db.commit()

    except sqlite3.IntegrityError:
        db.close()
        return "Assignment already exists", 409

    db.close()

    return {
        "message": "Judge assigned",
        "judge_id": judge_id,
        "project_id": project_id
    }, 201

init_db()

seed_users()
seed_event()
seed_tracks()
seed_teams()
seed_team_members()
seed_projects()
seed_scores()
seed_assignments()
seed_demo_sessions()


@app.get("/")
def home():
    return "Dogfood is alive! 🐺"

@app.get("/api/judge/projects")
def judge_projects():
    user, error = require_role("judge")

    if error:
        return error

    db = get_db()

    rows = db.execute(
        """
        SELECT
            projects.id,
            projects.title,
            projects.summary,
            projects.repo_url,
            projects.track_id
        FROM judge_assignments
        JOIN projects
            ON judge_assignments.project_id = projects.id
        WHERE judge_assignments.judge_id = ?
        ORDER BY projects.id
        """,
        (user[0],)
    ).fetchall()

    db.close()

    return {
        "projects": [
            {
                "id": row[0],
                "title": row[1],
                "summary": row[2],
                "repo_url": row[3],
                "track_id": row[4]
            }
            for row in rows
        ]
    }, 200

@app.post("/api/judge/scores")
def submit_judge_score():
    user, error = require_role("judge")

    if error:
        return error

    data = request.get_json()

    if not data:
        return "Invalid request", 400

    project_id = data.get("project_id")
    criterion_scores = data.get("scores", {})
    comment = data.get("comment", "")

    if project_id is None:
        return "project_id is required", 400

    if not criterion_scores:
        return "scores are required", 400

    db = get_db()

    assignment = db.execute(
        """
        SELECT 1
        FROM judge_assignments
        WHERE judge_id = ? AND project_id = ?
        """,
        (user[0], project_id)
    ).fetchone()

    if assignment is None:
        db.close()
        return "Project is not assigned to this judge", 403

    project = db.execute(
        """
        SELECT
            projects.id,
            teams.event_id
        FROM projects
        JOIN teams
            ON projects.team_id = teams.id
        WHERE projects.id = ?
        """,
        (project_id,)
).fetchone()

    if project is None:
        db.close()
        return "Project not found", 404

    criterion_ids = []

    for criterion_id in criterion_scores:
        try:
            criterion_ids.append(int(criterion_id))
        except (TypeError, ValueError):
            db.close()
            return "Invalid criterion ID", 400

    if not criterion_ids:
        db.close()
        return "scores are required", 400

    placeholders = ",".join("?" for _ in criterion_ids)

    rubric_rows = db.execute(
        f"""
        SELECT id
        FROM rubric_criteria
        WHERE event_id = ?
        AND id IN ({placeholders})
        """,
        [project[1], *criterion_ids]
    ).fetchall()

    if len(rubric_rows) != len(set(criterion_ids)):
        db.close()
        return "Invalid rubric criterion", 400

    db.execute(
        """
        INSERT INTO scores
        (judge_id, project_id, comment)
        VALUES (?, ?, ?)
        ON CONFLICT(judge_id, project_id)
        DO UPDATE SET
            comment = excluded.comment
        """,
        (user[0], project_id, comment)
    )

    score_row = db.execute(
        """
        SELECT id
        FROM scores
        WHERE judge_id = ? AND project_id = ?
        """,
        (user[0], project_id)
    ).fetchone()

    score_id = score_row[0]

    db.execute(
        """
        DELETE FROM score_values
        WHERE score_id = ?
        """,
        (score_id,)
    )

    for criterion_id, value in criterion_scores.items():
        db.execute(
            """
            INSERT INTO score_values
            (score_id, criterion_id, value)
            VALUES (?, ?, ?)
            """,
            (score_id, int(criterion_id), value)
        )

    db.commit()
    db.close()

    return {
        "message": "Score saved",
        "project_id": project_id
    }, 200

@app.post("/login")
def login():
    email = request.form["email"]

    db = get_db()

    user = db.execute(
        "SELECT id, name, role FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if user is None:
        return "User not found", 401

    session_id = str(uuid.uuid4())

    db.execute(
        "INSERT INTO sessions (id, user_id, created_at) VALUES (?, ?, ?)",
        (session_id, user[0], datetime.now(timezone.utc).isoformat())
    )

    db.commit()
    db.close()

    return {
        "message": "Login successful",
        "session": session_id,
        "user": {
            "id": user[0],
            "name": user[1],
            "role": user[2]
        }
    }

@app.get("/api/export.csv")
def export_csv():
    user, error = require_role("organizer")

    if error:
        return error

    db = get_db()

    rows = db.execute(
        """
        SELECT
            scores.project_id,
            projects.title,
            scores.judge_id,
            users.name,
            scores.functionality,
            scores.quality,
            scores.comment
        FROM scores
        JOIN projects ON scores.project_id = projects.id
        JOIN users ON scores.judge_id = users.id
        ORDER BY scores.project_id, scores.judge_id
        """
    ).fetchall()

    db.close()

    lines = [
        "project_id,title,judge_id,judge_name,functionality,quality,comment"
    ]

    for row in rows:
        lines.append(
            ",".join(
                [
                    str(row[0]),
                    str(row[1]),
                    str(row[2]),
                    str(row[3]),
                    str(row[4]),
                    str(row[5]),
                    str(row[6] or "")
                ]
            )
        )

    csv_data = "\n".join(lines)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=judging-export.csv"
        }
    )

@app.get("/organizer/judging-progress")
def organizer_judging_progress_page():
    user, error = require_role("organizer")
    if error:
        return error

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Judging Progress</title>

        <style>
            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                color: #1f2937;
            }

            .container {
                max-width: 1100px;
                margin: 0 auto;
                padding: 40px 24px;
            }

            h1 {
                margin-bottom: 8px;
            }

            .subtitle {
                color: #6b7280;
                margin-top: 0;
                margin-bottom: 32px;
            }

            .cards {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 32px;
            }

            .card {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }

            .card-label {
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 8px;
            }

            .card-value {
                font-size: 28px;
                font-weight: bold;
            }

            .progress-section {
                background: white;
                border-radius: 10px;
                padding: 24px;
                margin-bottom: 32px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }

            .progress-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }

            .progress-percent {
                font-size: 22px;
                font-weight: bold;
            }

            .progress-track {
                width: 100%;
                height: 18px;
                background: #e5e7eb;
                border-radius: 999px;
                overflow: hidden;
            }

            .progress-bar {
                height: 100%;
                width: 0%;
                background: #2563eb;
                transition: width 0.3s ease;
            }

            .results-section {
                background: white;
                border-radius: 10px;
                padding: 24px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }

            .results-section h2 {
                margin-top: 0;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 16px;
            }

            th,
            td {
                text-align: left;
                padding: 12px;
                border-bottom: 1px solid #e5e7eb;
            }

            th {
                background: #f9fafb;
                font-size: 14px;
            }

            td {
                font-size: 14px;
            }

            .error {
                color: #b91c1c;
                margin-top: 12px;
            }

            @media (max-width: 800px) {
                .cards {
                    grid-template-columns: repeat(2, 1fr);
                }
            }

            @media (max-width: 500px) {
                .cards {
                    grid-template-columns: 1fr;
                }

                .container {
                    padding: 24px 16px;
                }

                .results-section {
                    overflow-x: auto;
                }

                table {
                    min-width: 600px;
                }
            }
        </style>
    </head>

    <body>
        <div class="container">

            <h1>Judging Progress</h1>
            <p class="subtitle">
                Organizer overview of review completion and normalized results.
            </p>

            <div class="cards">
                <div class="card">
                    <div class="card-label">Total Projects</div>
                    <div class="card-value" id="total-projects">—</div>
                </div>

                <div class="card">
                    <div class="card-label">Total Assignments</div>
                    <div class="card-value" id="total-assignments">—</div>
                </div>

                <div class="card">
                    <div class="card-label">Completed Reviews</div>
                    <div class="card-value" id="completed-reviews">—</div>
                </div>

                <div class="card">
                    <div class="card-label">Pending Reviews</div>
                    <div class="card-value" id="pending-reviews">—</div>
                </div>
            </div>

            <div class="progress-section">
                <div class="progress-header">
                    <strong>Review Completion</strong>
                    <span class="progress-percent" id="progress-percent">—%</span>
                </div>

                <div class="progress-track">
                    <div
                        class="progress-bar"
                        id="progress-bar"
                    ></div>
                </div>
            </div>

            <div class="results-section">
                <h2>Normalized Results</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Project</th>
                            <th>Reviews</th>
                            <th>Raw Average</th>
                            <th>Normalized Score</th>
                        </tr>
                    </thead>

                    <tbody id="normalized-results">
                        <tr>
                            <td colspan="4">Loading results...</td>
                        </tr>
                    </tbody>
                </table>

                <p
                    class="error"
                    id="results-error"
                    hidden
                >
                    Could not load normalized results.
                </p>
            </div>

        </div>

        <script>
            fetch("/api/organizer/judging-progress")
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Failed to load judging progress");
                    }

                    return response.json();
                })
                .then(data => {
                    document.getElementById("total-projects").textContent =
                        data.total_projects;

                    document.getElementById("total-assignments").textContent =
                        data.total_assignments;

                    document.getElementById("completed-reviews").textContent =
                        data.completed_reviews;

                    document.getElementById("pending-reviews").textContent =
                        data.pending_reviews;

                    document.getElementById("progress-percent").textContent =
                        data.progress_percent + "%";

                    document.getElementById("progress-bar").style.width =
                        data.progress_percent + "%";
                })
                .catch(error => {
                    document.getElementById("progress-percent").textContent =
                        "Error";

                    console.error(error);
                });


            fetch("/api/organizer/normalized-results")
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Failed to load normalized results");
                    }

                    return response.json();
                })
                .then(data => {
                    const tableBody =
                        document.getElementById("normalized-results");

                    tableBody.innerHTML = "";

                    for (const [projectId, result] of
                         Object.entries(data.results)) {

                        const row = document.createElement("tr");

                        const projectCell = document.createElement("td");
                        projectCell.textContent = projectId;

                        const reviewCell = document.createElement("td");
                        reviewCell.textContent = result.review_count;

                        const rawAverageCell =
                            document.createElement("td");
                        rawAverageCell.textContent = result.raw_average;

                        const normalizedCell =
                            document.createElement("td");
                        normalizedCell.textContent =
                            result.normalized_score;

                        row.appendChild(projectCell);
                        row.appendChild(reviewCell);
                        row.appendChild(rawAverageCell);
                        row.appendChild(normalizedCell);

                        tableBody.appendChild(row);
                    }
                })
                .catch(error => {
                    document.getElementById("normalized-results").innerHTML =
                        "<tr><td colspan='4'>Unable to load results.</td></tr>";

                    document.getElementById("results-error").hidden = false;

                    console.error(error);
                });
        </script>
    </body>
    </html>
    """


@app.get("/api/organizer/judging-progress")
def judging_progress():
    user, error = require_role("organizer")
    if error:
        return error

    db = get_db()

    total_projects = db.execute(
        """
        SELECT COUNT(*)
        FROM projects
        WHERE status = 'submitted'
        """
    ).fetchone()[0]

    total_assignments = db.execute(
        """
        SELECT COUNT(*)
        FROM judge_assignments
        """
    ).fetchone()[0]

    completed_reviews = db.execute(
        """
        SELECT COUNT(*)
        FROM scores
        """
    ).fetchone()[0]

    pending_reviews = total_assignments - completed_reviews

    if total_assignments > 0:
        progress_percent = (
            completed_reviews / total_assignments
        ) * 100
    else:
        progress_percent = 0

    db.close()

    return {
        "total_projects": total_projects,
        "total_assignments": total_assignments,
        "completed_reviews": completed_reviews,
        "pending_reviews": pending_reviews,
        "progress_percent": round(progress_percent, 2)
    }

@app.get("/api/organizer/normalized-results")
def organizer_normalized_results():
    user, error = require_role("organizer")
    if error:
        return error

    db = get_db()

    results = calculate_normalized_scores(db)

    db.close()

    rounded_results = {}

    for project_id, result in results.items():
        normalized_score = round(
            result["normalized_score"], 3
        )

        if normalized_score == 0:
            normalized_score = 0.0

        rounded_results[project_id] = {
            "review_count": result["review_count"],
            "raw_average": round(result["raw_average"], 2),
            "normalized_score": normalized_score
        }

    return {
        "results": rounded_results
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
