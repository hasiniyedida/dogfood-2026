import json
from db import get_db


def seed_users():
    with open("fixtures.json", "r") as file:
        data = json.load(file)

    db = get_db()

    for judge in data["judges"]:
        db.execute(
            """
            INSERT OR IGNORE INTO users (name, email, role)
            VALUES (?, ?, ?)
            """,
            (judge["name"], judge["email"], "judge")
        )
    for team in data["teams"]:
        for email in team["members"]:
            db.execute(
                """
                INSERT OR IGNORE INTO users (name, email, role)
                VALUES (?, ?, ?)
                """,
                (email.split("@")[0], email, "participant")
            )
    db.commit()
    db.close()

def seed_event():
    with open("fixtures.json", "r") as file:
        data = json.load(file)

    db = get_db()

    event = data["event"]

    db.execute(
        """
        INSERT OR IGNORE INTO events
        (id, name, submissions_open, submissions_close)
        VALUES (?, ?, ?, ?)
        """,
        (
            event["id"],
            event["name"],
            "2026-01-01T00:00:00Z",
            event["submissions_close"]
        )
    )

    db.commit()
    db.close()

def seed_tracks():
    with open("fixtures.json", "r") as file:
        data = json.load(file)

    db = get_db()

    for track in data["tracks"]:
        db.execute(
            """
            INSERT OR IGNORE INTO tracks (id, event_id, name)
            VALUES (?, ?, ?)
            """,
            (
                track["id"],
                data["event"]["id"],
                track["name"]
            )
        )

    db.commit()
    db.close()

def seed_teams():
    with open("fixtures.json", "r") as file:
        data = json.load(file)

    db = get_db()

    for team in data["teams"]:
        db.execute(
            """
            INSERT OR IGNORE INTO teams (id, name, event_id)
            VALUES (?, ?, ?)
            """,
            (
                team["id"],
                team["name"],
                data["event"]["id"]
            )
        )
    db.commit()
    db.close()

def seed_team_members():
    with open("fixtures.json", "r") as file:
        data = json.load(file)

    db = get_db()

    for team in data["teams"]:
        for email in team["members"]:
            user = db.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,)
            ).fetchone()

            if user:
                db.execute(
                    """
                    INSERT OR IGNORE INTO team_members (team_id, user_id)
                    VALUES (?, ?)
                    """,
                    (team["id"], user[0])
                )
    db.commit()
    db.close()

def seed_projects():
    with open("fixtures.json", "r") as file:
        data = json.load(file)

    db = get_db()

    for project in data["projects"]:
        db.execute(
            """
            INSERT OR IGNORE INTO projects
            (id, team_id, track_id, title, summary, repo_url,
             submitted_at, updated_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project["id"],
                project["team"],
                project["track"],
                project["title"],
                project["summary"],
                project["repo_url"],
                project["submitted_at"],
                project["submitted_at"],
                "submitted"
            )
        )

    db.commit()
    db.close()

def seed_scores():
    with open("fixtures.json", "r") as file:
        data = json.load(file)

    db = get_db()

    for score in data["scores"]:
        judge = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (next(
                judge["email"]
                for judge in data["judges"]
                if judge["id"] == score["judge"]
            ),)
        ).fetchone()

        if judge:
            db.execute(
                """
                INSERT OR IGNORE INTO scores
                (judge_id, project_id, functionality, quality, comment)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    judge[0],
                    score["project"],
                    score["criteria"].get("functionality"),
                    score["criteria"].get("quality"),
                    score.get("comment", "")
                )
            )
    db.commit()
    db.close()

def seed_assignments():
    with open("fixtures.json", "r") as file:
        data = json.load(file)

    db = get_db()

    for score in data["scores"]:
        judge = next(
            judge
            for judge in data["judges"]
            if judge["id"] == score["judge"]
        )

        user = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (judge["email"],)
        ).fetchone()

        if user:
            db.execute(
                """
                INSERT OR IGNORE INTO judge_assignments
                (judge_id, project_id)
                VALUES (?, ?)
                """,
                (user[0], score["project"])
            )

    db.commit()
    db.close()

def seed_demo_sessions():
    with open("fixtures.json", "r") as file:
        data = json.load(file)

    db = get_db()

    # Find judges who actually have scores in the fixture.
    scored_judge_ids = []

    for score in data["scores"]:
        if score["judge"] not in scored_judge_ids:
            scored_judge_ids.append(score["judge"])

    judge_a = next(
        judge for judge in data["judges"]
        if judge["id"] == scored_judge_ids[0]
    )

    judge_b = next(
        judge for judge in data["judges"]
        if judge["id"] == scored_judge_ids[1]
    )

    # These two roles do not exist in the fixture, so we create
    # deterministic demo users for the acceptance checker.
    db.execute(
    """
    INSERT OR IGNORE INTO users (name, email, role)
    VALUES (?, ?, ?)
    """,
    ("Organizer", "organizer@example.org", "organizer")
)

    db.execute(
        """
        INSERT OR IGNORE INTO users (name, email, role)
        VALUES (?, ?, ?)
        """,
        ("Admin", "admin@example.org", "admin")
    )

    db.execute(
        """
        INSERT OR IGNORE INTO users (name, email, role)
        VALUES (?, ?, ?)
        """,
        ("Participant", "participant@example.org", "participant")
    )

    participant = db.execute(
        "SELECT id FROM users WHERE email = ?",
        ("participant@example.org",)
    ).fetchone()

    if participant:
        db.execute(
            """
            INSERT OR IGNORE INTO team_members
            (team_id, user_id)
            VALUES (?, ?)
            """,
            ("tm_01", participant[0])
        )

    demo_sessions = [
        ("org_7f2a", "organizer@example.org"),
        ("jdg_a_91bc", judge_a["email"]),
        ("jdg_b_44de", judge_b["email"]),
        ("prt_2e88", "participant@example.org"),
        ("adm_3c91", "admin@example.org")
    ]

    for session_id, email in demo_sessions:
        user = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user:
            db.execute(
                """
                INSERT OR REPLACE INTO sessions
                (id, user_id, created_at)
                VALUES (?, ?, datetime('now'))
                """,
                (session_id, user[0])
            )

    db.commit()
    db.close()

if __name__ == "__main__":
    seed_users()
    seed_event()
    seed_tracks()
    seed_teams()
    seed_team_members()
    seed_projects()
    seed_scores() 
    seed_assignments() 
    seed_demo_sessions()
    print("Seed functions completed.")