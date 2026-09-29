from pydoc import html

from flask import Flask, request, Response, redirect
from db import init_db, get_db
from normalization import calculate_normalized_scores
import sqlite3
from seed import seed_users, seed_event, seed_rubric, seed_tracks, seed_teams, seed_team_members, seed_projects, seed_scores, seed_assignments, seed_demo_sessions
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

@app.get("/participant")
def participant_workspace():
    user, error = require_role("participant")

    if error:
        return error

    db = get_db()

    teams = db.execute(
        """
        SELECT teams.id, teams.name
        FROM teams
        JOIN team_members
            ON teams.id = team_members.team_id
        WHERE team_members.user_id = ?
        ORDER BY teams.name
        """,
        (user[0],)
    ).fetchall()

    tracks = db.execute(
        """
        SELECT id, name
        FROM tracks
        ORDER BY name
        """
    ).fetchall()

    db.close()

    team_options = "".join(
        f'<option value="{team[0]}">{team[1]}</option>'
        for team in teams
    )

    track_options = "".join(
        f'<option value="{track[0]}">{track[1]}</option>'
        for track in tracks
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <title>Participant Workspace — Dogfood 2026</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                color: #1f2937;
            }}

            .container {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 40px 24px;
            }}

            .header {{
                margin-bottom: 32px;
            }}

            h1 {{
                margin: 0 0 8px;
            }}

            .subtitle {{
                color: #6b7280;
                margin: 0;
                line-height: 1.5;
            }}

            .card {{
                background: white;
                border-radius: 10px;
                padding: 28px;
                margin-bottom: 24px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }}

            .card h2 {{
                margin-top: 0;
                margin-bottom: 8px;
            }}

            .card-description {{
                color: #6b7280;
                margin-top: 0;
                margin-bottom: 24px;
            }}

            .form-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}

            .form-group {{
                margin-bottom: 4px;
            }}

            .full-width {{
                grid-column: 1 / -1;
            }}

            label {{
                display: block;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 8px;
            }}

            input,
            textarea,
            select {{
                width: 100%;
                padding: 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-family: Arial, sans-serif;
                font-size: 14px;
                background: white;
            }}

            textarea {{
                min-height: 120px;
                resize: vertical;
            }}

            input:focus,
            textarea:focus,
            select:focus {{
                outline: none;
                border-color: #2563eb;
            }}

            button {{
                border: none;
                border-radius: 8px;
                padding: 12px 18px;
                background: #2563eb;
                color: white;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
            }}

            button:hover {{
                background: #1d4ed8;
            }}

            button:disabled {{
                background: #9ca3af;
                cursor: not-allowed;
            }}

            .message {{
                margin-top: 16px;
                padding: 12px 14px;
                border-radius: 8px;
                display: none;
                line-height: 1.5;
                font-size: 14px;
            }}

            .message.success {{
                display: block;
                background: #dcfce7;
                color: #166534;
            }}

            .message.error {{
                display: block;
                background: #fee2e2;
                color: #991b1b;
            }}

            .projects {{
                display: grid;
                gap: 16px;
            }}

            .project-card {{
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 20px;
            }}

            .project-card h3 {{
                margin-top: 0;
                margin-bottom: 8px;
            }}

            .project-meta {{
                color: #6b7280;
                font-size: 13px;
                margin-bottom: 16px;
            }}

            .status {{
                display: inline-block;
                padding: 5px 9px;
                border-radius: 999px;
                background: #eff6ff;
                color: #2563eb;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 14px;
            }}

            .project-summary {{
                line-height: 1.5;
                margin-bottom: 16px;
            }}

            .project-actions {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}

            .secondary {{
                background: #e5e7eb;
                color: #1f2937;
            }}

            .secondary:hover {{
                background: #d1d5db;
            }}

            .empty {{
                color: #6b7280;
                margin: 0;
            }}

            .navigation {{
                margin-top: 24px;
            }}

            .navigation a {{
                color: #2563eb;
                text-decoration: none;
                font-size: 14px;
                margin-right: 18px;
            }}

            @media (max-width: 700px) {{
                .form-grid {{
                    grid-template-columns: 1fr;
                }}

                .full-width {{
                    grid-column: auto;
                }}

                .container {{
                    padding: 24px 16px;
                }}
            }}
        </style>
    </head>

    <body>

        <div class="container">

            <div class="header">
                <h1>Participant Workspace</h1>

                <p class="subtitle">
                    Welcome, {user[1]}. Create, edit, and submit your hackathon project.
                </p>
            </div>

            <div class="card">

                <h2>Create a project draft</h2>

                <p class="card-description">
                    Start with a draft. You can edit it until the submission deadline.
                </p>

                <form id="create-form">

                    <div class="form-grid">

                        <div class="form-group">
                            <label for="team">Team</label>

                            <select id="team" required>
                                <option value="">Select your team</option>
                                {team_options}
                            </select>
                        </div>

                        <div class="form-group">
                            <label for="track">Track</label>

                            <select id="track" required>
                                <option value="">Select a track</option>
                                {track_options}
                            </select>
                        </div>

                        <div class="form-group full-width">
                            <label for="title">Project title</label>

                            <input
                                id="title"
                                type="text"
                                placeholder="Enter your project title"
                                required
                            >
                        </div>

                        <div class="form-group full-width">
                            <label for="summary">Summary</label>

                            <textarea
                                id="summary"
                                placeholder="Describe your project"
                                required
                            ></textarea>
                        </div>

                        <div class="form-group full-width">
                            <label for="repo-url">Repository URL</label>

                            <input
                                id="repo-url"
                                type="url"
                                placeholder="https://github.com/..."
                            >
                        </div>

                    </div>

                    <div style="margin-top: 20px;">
                        <button type="submit">
                            Create Draft
                        </button>
                    </div>

                </form>

                <div id="create-message" class="message"></div>

            </div>

            <div class="card">

                <h2>My projects</h2>

                <p class="card-description">
                    View your team's project drafts and submissions.
                </p>

                <div id="projects" class="projects">
                    <p class="empty">Loading projects...</p>
                </div>

            </div>

            <div class="navigation">
                <a href="/portal">← Portal</a>
                <a href="/">Home</a>
                <a href="/projects">Project Gallery</a>
            </div>

        </div>

        <script>
            async function loadProjects() {{
                const container =
                    document.getElementById("projects");

                const response =
                    await fetch("/api/participant/projects");

                const data =
                    await response.json().catch(() => null);

                if (!response.ok) {{
                    container.innerHTML =
                        '<p class="empty">Could not load projects.</p>';
                    return;
                }}

                if (!data.projects || data.projects.length === 0) {{
                    container.innerHTML =
                        '<p class="empty">You do not have any projects yet.</p>';
                    return;
                }}

                container.innerHTML = "";

                for (const project of data.projects) {{
                    const card =
                        document.createElement("div");

                    card.className = "project-card";

                    card.innerHTML = `
                        <div class="status">
                            ${{project.status.toUpperCase()}}
                        </div>

                        <h3></h3>

                        <div class="project-meta"></div>

                        <p class="project-summary"></p>

                        <div class="project-actions"></div>
                    `;

                    card.querySelector("h3").textContent =
                        project.title;

                    card.querySelector(".project-meta").textContent =
                        project.team_name +
                        " · " +
                        project.track_name;

                    card.querySelector(".project-summary").textContent =
                        project.summary;

                    const actions =
                        card.querySelector(".project-actions");

                    if (project.repo_url) {{
                        const repo =
                            document.createElement("a");

                        repo.href = project.repo_url;
                        repo.target = "_blank";
                        repo.rel = "noopener noreferrer";
                        repo.textContent = "Repository";
                        repo.style.color = "#2563eb";
                        repo.style.textDecoration = "none";
                        repo.style.fontWeight = "bold";
                        repo.style.padding = "12px 0";

                        actions.appendChild(repo);
                    }}

                    if (project.status === "draft") {{
                        const editButton =
                            document.createElement("button");

                        editButton.textContent =
                            "Edit Draft";

                        editButton.onclick = function() {{
                            editProject(project);
                        }};

                        actions.appendChild(editButton);

                        const submitButton =
                            document.createElement("button");

                        submitButton.textContent =
                            "Submit Project";

                        submitButton.className = "secondary";

                        submitButton.onclick = function() {{
                            submitProject(project.id, submitButton);
                        }};

                        actions.appendChild(submitButton);
                    }}

                    container.appendChild(card);
                }}
            }}

            async function createProject(event) {{
                event.preventDefault();

                const message =
                    document.getElementById("create-message");

                const formData =
                    new FormData();

                formData.append(
                    "team_id",
                    document.getElementById("team").value
                );

                formData.append(
                    "track_id",
                    document.getElementById("track").value
                );

                formData.append(
                    "title",
                    document.getElementById("title").value.trim()
                );

                formData.append(
                    "summary",
                    document.getElementById("summary").value.trim()
                );

                formData.append(
                    "repo_url",
                    document.getElementById("repo-url").value.trim()
                );

                message.textContent = "Creating draft...";
                message.className = "message success";

                const response =
                    await fetch("/projects/new", {{
                        method: "POST",
                        body: formData
                    }});

                const data =
                    await response.json().catch(() => null);

                if (!response.ok) {{
                    message.textContent =
                        data || "Could not create draft.";

                    message.className = "message error";
                    return;
                }}

                message.textContent =
                    "Draft created successfully.";

                message.className = "message success";

                document
                    .getElementById("create-form")
                    .reset();

                await loadProjects();
            }}

            async function editProject(project) {{
                const title =
                    prompt(
                        "Project title:",
                        project.title
                    );

                if (title === null) {{
                    return;
                }}

                const summary =
                    prompt(
                        "Project summary:",
                        project.summary
                    );

                if (summary === null) {{
                    return;
                }}

                const repoUrl =
                    prompt(
                        "Repository URL:",
                        project.repo_url || ""
                    );

                if (repoUrl === null) {{
                    return;
                }}

                const formData =
                    new FormData();

                formData.append("title", title);
                formData.append("summary", summary);
                formData.append("repo_url", repoUrl);

                const response =
                    await fetch(
                        "/projects/" +
                        encodeURIComponent(project.id),
                        {{
                            method: "PUT",
                            body: formData
                        }}
                    );

                const data =
                    await response.json().catch(() => null);

                if (!response.ok) {{
                    alert(data || "Could not update project.");
                    return;
                }}

                await loadProjects();
            }}

            async function submitProject(projectId, button) {{
                button.disabled = true;
                button.textContent = "Submitting...";

                const response =
                    await fetch(
                        "/projects/" +
                        encodeURIComponent(projectId) +
                        "/submit",
                        {{
                            method: "POST"
                        }}
                    );

                const data =
                    await response.json().catch(() => null);

                if (!response.ok) {{
                    alert(data || "Could not submit project.");

                    button.disabled = false;
                    button.textContent = "Submit Project";
                    return;
                }}

                await loadProjects();
            }}

            document
                .getElementById("create-form")
                .addEventListener(
                    "submit",
                    createProject
                );

            loadProjects();
        </script>

    </body>
    </html>
    """

@app.get("/admin")
def admin_workspace():
    user, error = require_role("admin")

    if error:
        return error

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Workspace | Dogfood 2026</title>

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

            .topbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 20px;
                margin-bottom: 32px;
            }

            h1 {
                margin: 0 0 8px 0;
                font-size: 32px;
            }

            .subtitle {
                margin: 0;
                color: #6b7280;
            }

            .nav {
                display: flex;
                gap: 16px;
                flex-wrap: wrap;
            }

            .nav a {
                color: #2563eb;
                text-decoration: none;
                font-weight: 600;
            }

            .card {
                background: white;
                border-radius: 10px;
                padding: 24px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }

            .role {
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                background: #eff6ff;
                color: #2563eb;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 14px;
            }

            .card h2 {
                margin: 0 0 10px 0;
                font-size: 21px;
            }

            .card p {
                color: #6b7280;
                line-height: 1.5;
                margin: 0;
            }

            .actions {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 16px;
                margin-top: 24px;
            }

            .action {
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 20px;
                text-decoration: none;
                color: #1f2937;
                transition: box-shadow 0.15s ease;
            }

            .action:hover {
                box-shadow: 0 3px 10px rgba(0,0,0,0.08);
            }

            .action h3 {
                margin: 0 0 8px 0;
                color: #2563eb;
                font-size: 17px;
            }

            .action p {
                font-size: 14px;
            }

            @media (max-width: 700px) {
                .container {
                    padding: 28px 16px;
                }

                .topbar {
                    align-items: flex-start;
                    flex-direction: column;
                }

                .actions {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>

    <body>

        <div class="container">

            <div class="topbar">
                <div>
                    <h1>Admin Workspace</h1>
                    <p class="subtitle">
                        Administrative access for Dogfood 2026.
                    </p>
                </div>

                <div class="nav">
                    <a href="/portal">Portal</a>
                    <a href="/">Home</a>
                </div>
            </div>

            <div class="card">

                <span class="role">ADMIN</span>

                <h2>Welcome, Admin</h2>

                <p>
                    This workspace is reserved for administrative
                    management of the Dogfood portal.
                </p>

                <div class="actions">

                    <a class="action" href="/portal">
                        <h3>Role Portal</h3>
                        <p>
                            Return to the role-based portal and
                            access available workspaces.
                        </p>
                    </a>

                    <a class="action" href="/projects">
                        <h3>Project Gallery</h3>
                        <p>
                            View the public collection of submitted
                            hackathon projects.
                        </p>
                    </a>

                </div>

            </div>

        </div>

    </body>
    </html>
    """

@app.get("/judge")
def judge_workspace():
    user, error = require_role("judge")

    if error:
        return error

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Judge Workspace</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
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

            .header {
                margin-bottom: 28px;
            }

            .header h1 {
                margin: 0 0 8px;
                font-size: 32px;
            }

            .header p {
                margin: 0;
                color: #6b7280;
            }

            .card {
                background: white;
                border-radius: 10px;
                padding: 24px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }

            .card h2 {
                margin-top: 0;
                margin-bottom: 8px;
            }

            .muted {
                color: #6b7280;
            }

            .project-card {
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 20px;
                margin-top: 16px;
            }

            .project-card h3 {
                margin: 0 0 6px;
            }

            .track {
                display: inline-block;
                margin-bottom: 14px;
                padding: 5px 9px;
                border-radius: 999px;
                background: #eff6ff;
                color: #2563eb;
                font-size: 13px;
                font-weight: bold;
            }

            .repo {
                display: inline-block;
                margin: 8px 0 18px;
                color: #2563eb;
                text-decoration: none;
                font-weight: bold;
            }

            .criterion {
                margin-top: 18px;
            }

            .criterion label {
                display: block;
                margin-bottom: 7px;
                font-weight: bold;
            }

            .criterion input,
            .criterion textarea {
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #d1d5db;
                border-radius: 7px;
                font: inherit;
            }

            .criterion input {
                max-width: 180px;
            }

            .criterion textarea {
                min-height: 90px;
                resize: vertical;
            }

            .weight {
                color: #6b7280;
                font-size: 13px;
                font-weight: normal;
            }

            button {
                margin-top: 20px;
                padding: 11px 16px;
                border: none;
                border-radius: 7px;
                background: #2563eb;
                color: white;
                font-weight: bold;
                cursor: pointer;
            }

            button:hover {
                opacity: 0.92;
            }

            .message {
                margin-top: 12px;
                color: #2563eb;
                font-weight: bold;
            }

            .nav {
                margin-top: 28px;
            }

            .nav a {
                margin-right: 18px;
                color: #2563eb;
                text-decoration: none;
                font-weight: bold;
            }

            @media (max-width: 700px) {
                .container {
                    padding: 24px 16px;
                }

                .header h1 {
                    font-size: 28px;
                }
            }
        </style>
    </head>

    <body>
        <div class="container">

            <div class="header">
                <h1>Judge Workspace</h1>
                <p>Welcome, Judge. Review your assigned projects and submit scores.</p>
            </div>

            <div class="card">
                <h2>Assigned Projects</h2>
                <p class="muted">
                    Score each assigned project using the event rubric.
                </p>

                <div id="projects">
                    Loading assigned projects...
                </div>
            </div>

            <div class="nav">
                <a href="/portal">← Portal</a>
                <a href="/">Home</a>
                <a href="/projects">Project Gallery</a>
            </div>

        </div>

        <script>
            async function loadJudgeWorkspace() {
                const projectsBox = document.getElementById("projects");

                try {
                    const projectsResponse = await fetch("/api/judge/projects");

                    if (!projectsResponse.ok) {
                        projectsBox.textContent = "Could not load assigned projects.";
                        return;
                    }

                    const projectsData = await projectsResponse.json();
                    judgeEventId = projectsData.event_id;

                    const rubricResponse =
                        await fetch(`/api/events/${judgeEventId}/rubric`);

                    if (!rubricResponse.ok) {
                        projectsBox.textContent = "Could not load judging rubric.";
                        return;
                    }

                    const rubricData = await rubricResponse.json();;

                    if (!projectsResponse.ok) {
                        projectsBox.textContent = "Could not load assigned projects.";
                        return;
                    }

                    if (!rubricResponse.ok) {
                        projectsBox.textContent = "Could not load judging rubric.";
                        return;
                    }

                    if (projectsData.projects.length === 0) {
                        projectsBox.innerHTML =
                            '<p class="muted">You have no assigned projects.</p>';
                        return;
                    }

                    projectsBox.innerHTML = "";

                    projectsData.projects.forEach(project => {
                        const card = document.createElement("div");
                        card.className = "project-card";

                        const criteriaHTML = rubricData.criteria.map(criterion => `
                            <div class="criterion">
                                <label>
                                    ${criterion.name}
                                    <span class="weight">
                                        (${criterion.weight}%)
                                    </span>
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    max="5"
                                    step="0.5"
                                    id="score-${project.id}-${criterion.id}"
                                    placeholder="0–5"
                                >
                            </div>
                        `).join("");

                        card.innerHTML = `
                            <h3>${project.title}</h3>
                            <span class="track">${project.track_id}</span>
                            <p>${project.summary}</p>

                            ${
                                project.repo_url
                                ? `<a class="repo"
                                      href="${project.repo_url}"
                                      target="_blank">
                                      View repository →
                                   </a>`
                                : ""
                            }

                            ${criteriaHTML}

                            <div class="criterion">
                                <label>Comment</label>
                                <textarea
                                    id="comment-${project.id}"
                                    placeholder="Add judging feedback..."
                                ></textarea>
                            </div>

                            <button onclick="saveScore('${project.id}')">
                                Save Score
                            </button>

                            <div
                                class="message"
                                id="message-${project.id}">
                            </div>
                        `;

                        projectsBox.appendChild(card);
                    });

                } catch (error) {
                    projectsBox.textContent =
                        "Could not load the judge workspace.";
                }
            }

            async function saveScore(projectId) {
                const rubricResponse =
                    await fetch(`/api/events/${judgeEventId}/rubric`);

                const rubricData = await rubricResponse.json();

                const scores = {};

                for (const criterion of rubricData.criteria) {
                    const input = document.getElementById(
                        `score-${projectId}-${criterion.id}`
                    );

                    if (!input.value) {
                        document.getElementById(
                            `message-${projectId}`
                        ).textContent =
                            "Please enter a score for every criterion.";

                        return;
                    }

                    const value = Number(input.value);

                    if (value < 0 || value > 5) {
                        document.getElementById(
                            `message-${projectId}`
                        ).textContent =
                            "Scores must be between 0 and 5.";

                        return;
                    }

                    scores[String(criterion.id)] = value;
                }

                const comment =
                    document.getElementById(
                        `comment-${projectId}`
                    ).value;

                const response = await fetch(
                    "/api/judge/scores",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            project_id: projectId,
                            scores: scores,
                            comment: comment
                        })
                    }
                );

                const message =
                    document.getElementById(
                        `message-${projectId}`
                    );

                if (response.ok) {
                    message.textContent = "Score saved successfully.";
                } else {
                    const text = await response.text();
                    message.textContent = text;
                }
            }

            loadJudgeWorkspace();
        </script>
    </body>
    </html>
    """

@app.get("/portal")
def portal():
    user = get_current_user()

    if user is None:
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sign in — Dogfood 2026</title>
            <style>
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

                .card {
                    max-width: 500px;
                    margin: 60px auto;
                    background: white;
                    border-radius: 10px;
                    padding: 32px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                }

                h1 {
                    margin-top: 0;
                }

                p {
                    color: #6b7280;
                }

                a {
                    display: inline-block;
                    margin-top: 12px;
                    padding: 12px 18px;
                    border-radius: 8px;
                    background: #2563eb;
                    color: white;
                    text-decoration: none;
                    font-weight: bold;
                }
            </style>
        </head>

        <body>
            <div class="container">
                <div class="card">
                    <h1>Sign in required</h1>
                    <p>Please sign in to access your Dogfood portal.</p>
                    <a href="/login">Sign in</a>
                </div>
            </div>
        </body>
        </html>
        """, 401

    role = user[3]

    destinations = {
        "participant": (
            "Participant Workspace",
            "Create, edit, and submit your hackathon project.",
            "/participant"
        ),
        "judge": (
            "Judge Workspace",
            "Review your assigned projects and submit scores.",
            "/judge"
        ),
        "organizer": (
            "Organizer Dashboard",
            "Monitor judging progress and review results.",
            "/organizer/judging-progress"
        ),
        "admin": (
            "Admin Workspace",
            "Manage administrative access to the Dogfood portal.",
            "/admin"
        )
    }

    destination = destinations.get(role)

    if destination is None:
        return "Unknown role", 403

    title, description, link = destination

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Portal — Dogfood 2026</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                color: #1f2937;
            }}

            .container {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 40px 24px;
            }}

            .header {{
                margin-bottom: 32px;
            }}

            h1 {{
                margin: 0 0 8px;
            }}

            .subtitle {{
                color: #6b7280;
                margin: 0;
            }}

            .card {{
                background: white;
                border-radius: 10px;
                padding: 28px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }}

            .role {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                background: #eff6ff;
                color: #2563eb;
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 16px;
            }}

            h2 {{
                margin: 0 0 8px;
            }}

            .description {{
                color: #6b7280;
                line-height: 1.5;
                margin-bottom: 24px;
            }}

            .button {{
                display: inline-block;
                padding: 12px 18px;
                border-radius: 8px;
                background: #2563eb;
                color: white;
                text-decoration: none;
                font-size: 14px;
                font-weight: bold;
            }}

            .navigation {{
                margin-top: 24px;
            }}

            .navigation a {{
                color: #2563eb;
                text-decoration: none;
                font-size: 14px;
                margin-right: 18px;
            }}

            @media (max-width: 500px) {{
                .container {{
                    padding: 24px 16px;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <div class="header">
                <h1>Dogfood 2026 🐺</h1>
                <p class="subtitle">
                    Welcome, {user[1]}.
                </p>
            </div>

            <div class="card">
                <div class="role">{role.title()}</div>

                <h2>{title}</h2>

                <p class="description">
                    {description}
                </p>

                <a class="button" href="{link}">
                    Open Workspace →
                </a>

                <div class="navigation">
                    <a href="/">← Home</a>
                    <a href="/projects">Project Gallery</a>
                </div>
            </div>

        </div>
    </body>
    </html>
    """


@app.get("/organizer-test")
def organizer_test():
    user, error = require_role("organizer")

    if error:
        return error

    return f"Hello {user[1]}, you are the organizer."

@app.get("/projects")
def gallery():
    db = get_db()

    event = db.execute(
        "SELECT id FROM events ORDER BY id LIMIT 1"
    ).fetchone()

    event_id = event[0] if event else ""

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

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Gallery | Dogfood 2026</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                color: #1f2937;
            }}

            .container {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 40px 24px;
            }}

            .topbar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
                margin-bottom: 32px;
            }}

            h1 {{
                margin: 0 0 8px 0;
                font-size: 32px;
            }}

            .subtitle {{
                margin: 0;
                color: #6b7280;
            }}

            .nav {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}

            .nav a {{
                text-decoration: none;
                color: #2563eb;
                font-weight: 600;
            }}

            .filters {{
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 24px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }}

            .filter-form {{
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }}

            input,
            select {{
                padding: 11px 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 14px;
            }}

            input {{
                flex: 1;
                min-width: 220px;
            }}

            button {{
                border: none;
                border-radius: 8px;
                padding: 11px 18px;
                background: #2563eb;
                color: white;
                font-weight: 600;
                cursor: pointer;
            }}

            .count {{
                color: #6b7280;
                margin: 0 0 18px 0;
                font-size: 14px;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 20px;
            }}

            .card {{
                background: white;
                border-radius: 10px;
                padding: 22px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                display: flex;
                flex-direction: column;
                min-height: 210px;
            }}

            .track {{
                display: inline-block;
                align-self: flex-start;
                padding: 5px 9px;
                border-radius: 999px;
                background: #eff6ff;
                color: #2563eb;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 12px;
            }}

            .card h2 {{
                margin: 0 0 10px 0;
                font-size: 21px;
            }}

            .summary {{
                color: #6b7280;
                line-height: 1.5;
                margin: 0 0 18px 0;
                flex: 1;
            }}

            .card-footer {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 12px;
                font-size: 13px;
            }}

            .date {{
                color: #6b7280;
            }}

            .repo {{
                color: #2563eb;
                text-decoration: none;
                font-weight: 600;
            }}

            .empty {{
                background: white;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                color: #6b7280;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }}

            @media (max-width: 700px) {{
                .container {{
                    padding: 28px 16px;
                }}

                .topbar {{
                    align-items: flex-start;
                    flex-direction: column;
                }}

                .grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>

    <body>

    <div class="container">

        <div class="topbar">
            <div>
                <h1>Project Gallery</h1>
                <p class="subtitle">
                    Explore submitted projects from Dogfood 2026.
                </p>
            </div>

            <div class="nav">
                <a href="/">Home</a>
                <a href="/events/{event_id}/community-vote">Community Voting</a>
                <a href="/login">Sign in</a>
            </div>
        </div>

        <div class="filters">
            <form method="get" class="filter-form">

                <input
                    type="text"
                    name="search"
                    placeholder="Search projects..."
                    value="{search}"
                >

                <select name="track">
                    <option value="">All tracks</option>

                    <option value="trk_01" {"selected" if track_id == "trk_01" else ""}>
                        Developer tools
                    </option>

                    <option value="trk_02" {"selected" if track_id == "trk_02" else ""}>
                        Data and analytics
                    </option>

                    <option value="trk_03" {"selected" if track_id == "trk_03" else ""}>
                        Accessibility
                    </option>

                    <option value="trk_04" {"selected" if track_id == "trk_04" else ""}>
                        Security
                    </option>

                    <option value="trk_05" {"selected" if track_id == "trk_05" else ""}>
                        Climate
                    </option>

                    <option value="trk_06" {"selected" if track_id == "trk_06" else ""}>
                        Health
                    </option>

                    <option value="trk_07" {"selected" if track_id == "trk_07" else ""}>
                        Education
                    </option>

                    <option value="trk_08" {"selected" if track_id == "trk_08" else ""}>
                        Open hardware
                    </option>
                </select>

                <button type="submit">Filter</button>

            </form>
        </div>

        <p class="count">
            {len(rows)} submitted project{"s" if len(rows) != 1 else ""} found
        </p>

        <div class="grid">

            {
                "".join(
                    f'''
                    <article class="card">

                        <span class="track">{row[6]}</span>

                        <h2>{row[1]}</h2>

                        <p class="summary">{row[2]}</p>

                        <div class="card-footer">

                            <span class="date">
                                Submitted {row[4]}
                            </span>

                            {
                                f'<a class="repo" href="{row[3]}" target="_blank">Repository →</a>'
                                if row[3]
                                else ''
                            }

                        </div>

                    </article>
                    '''
                    for row in rows
                )
            }

        </div>

        {
            '<div class="empty">No submitted projects match your search.</div>'
            if not rows
            else ''
        }

    </div>

    </body>
    </html>
    """, 200

@app.get("/events/<event_id>/community-vote")
def community_vote_page(event_id):
    db = get_db()

    event = db.execute(
        """
        SELECT id, name
        FROM events
        WHERE id = ?
        """,
        (event_id,)
    ).fetchone()

    db.close()

    if event is None:
        return "Event not found", 404

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Community Voting - {event[1]}</title>

        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f5f7fa;
                color: #1f2937;
            }}

            .container {{
                max-width: 1100px;
                margin: 0 auto;
                padding: 40px 24px;
            }}

            h1 {{
                margin-bottom: 8px;
            }}

            .subtitle {{
                color: #6b7280;
                margin-top: 0;
                margin-bottom: 32px;
            }}

            .token-section {{
                background: white;
                border-radius: 10px;
                padding: 24px;
                margin-bottom: 32px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }}

            .token-section h2 {{
                margin-top: 0;
            }}

            .token-row {{
                display: flex;
                gap: 12px;
                margin-top: 16px;
            }}

            .token-input {{
                flex: 1;
                padding: 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 14px;
            }}

            button {{
                border: none;
                border-radius: 8px;
                padding: 12px 18px;
                background: #2563eb;
                color: white;
                font-size: 14px;
                cursor: pointer;
            }}

            button:hover {{
                background: #1d4ed8;
            }}

            button:disabled {{
                background: #9ca3af;
                cursor: not-allowed;
            }}

            .message {{
                margin-top: 16px;
                color: #374151;
            }}

            .error {{
                color: #b91c1c;
            }}

            .success {{
                color: #166534;
            }}

            .projects {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 16px;
            }}

            .project-card {{
                background: white;
                border-radius: 10px;
                padding: 24px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }}

            .project-card h2 {{
                margin-top: 0;
                margin-bottom: 10px;
            }}

            .project-summary {{
                color: #6b7280;
                line-height: 1.5;
                margin-bottom: 20px;
            }}

            .project-card hr {{
                border: 0;
                border-top: 1px solid #e5e7eb;
                margin: 20px 0;
            }}

            .empty {{
                background: white;
                border-radius: 10px;
                padding: 24px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                color: #6b7280;
            }}

            @media (max-width: 700px) {{
                .projects {{
                    grid-template-columns: 1fr;
                }}

                .token-row {{
                    flex-direction: column;
                }}

                .container {{
                    padding: 24px 16px;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="container">

            <h1>Community Voting</h1>

            <p class="subtitle">
                Cast your community vote for a project in {event[1]}.
            </p>

            <div class="token-section">
                <h2>Access Ballot</h2>

                <p>
                    Enter your voter token to load the randomized ballot.
                </p>

                <div class="token-row">
                    <input
                        id="token"
                        class="token-input"
                        type="text"
                        placeholder="Enter voter token"
                    >

                    <button onclick="loadBallot()">
                        Load Ballot
                    </button>
                </div>

                <div
                    id="message"
                    class="message"
                ></div>
            </div>

            <div
                id="projects"
                class="projects"
            ></div>

        </div>

        <script>
            const eventId = {event_id!r};

            async function loadBallot() {{
                const token =
                    document.getElementById("token").value.trim();

                const message =
                    document.getElementById("message");

                const container =
                    document.getElementById("projects");

                if (!token) {{
                    message.textContent =
                        "Please enter your voter token.";

                    message.className = "message error";
                    return;
                }}

                message.textContent = "Loading ballot...";
                message.className = "message";

                container.innerHTML = "";

                const response = await fetch(
                    "/api/events/" +
                    encodeURIComponent(eventId) +
                    "/ballot?token=" +
                    encodeURIComponent(token)
                );

                const data =
                    await response.json().catch(() => null);

                if (!response.ok) {{
                    message.textContent =
                        data || "Could not load ballot.";

                    message.className = "message error";
                    return;
                }}

                message.textContent =
                    "Ballot loaded. Projects are shown in randomized order.";

                message.className = "message success";

                if (!data.projects ||
                    data.projects.length === 0) {{

                    container.innerHTML =
                        '<div class="empty">' +
                        'No projects are available for voting.' +
                        '</div>';

                    return;
                }}

                for (const project of data.projects) {{
                    const card =
                        document.createElement("div");

                    card.className = "project-card";

                    const title =
                        document.createElement("h2");

                    title.textContent = project.title;

                    const summary =
                        document.createElement("p");

                    summary.className = "project-summary";
                    summary.textContent = project.summary;

                    const button =
                        document.createElement("button");

                    button.textContent =
                        "Vote for this project";

                    button.onclick = function() {{
                        vote(project.id, button);
                    }};

                    card.appendChild(title);
                    card.appendChild(summary);
                    card.appendChild(button);

                    container.appendChild(card);
                }}
            }}

            async function vote(projectId, button) {{
                const token =
                    document.getElementById("token").value.trim();

                const message =
                    document.getElementById("message");

                button.disabled = true;
                button.textContent = "Submitting...";

                const response = await fetch(
                    "/api/community-vote",
                    {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/json"
                        }},
                        body: JSON.stringify({{
                            event_id: eventId,
                            token: token,
                            project_id: projectId
                        }})
                    }}
                );

                const data =
                    await response.json().catch(() => null);

                if (response.ok) {{
                    message.textContent =
                        "Vote recorded successfully.";

                    message.className = "message success";

                    document
                        .querySelectorAll("button")
                        .forEach(function(currentButton) {{
                            currentButton.disabled = true;
                        }});

                    return;
                }}

                message.textContent =
                    data || "Vote failed.";

                message.className = "message error";

                button.disabled = false;
                button.textContent =
                    "Vote for this project";
            }}
        </script>
    </body>
    </html>
    """

@app.get("/api/participant/projects")
def get_participant_projects():
    user, error = require_role("participant")

    if error:
        return error

    db = get_db()

    projects = db.execute(
        """
        SELECT
            projects.id,
            projects.team_id,
            teams.name,
            projects.track_id,
            tracks.name,
            projects.title,
            projects.summary,
            projects.repo_url,
            projects.status,
            projects.submitted_at,
            projects.updated_at
        FROM projects
        JOIN teams
            ON projects.team_id = teams.id
        JOIN team_members
            ON teams.id = team_members.team_id
        JOIN tracks
            ON projects.track_id = tracks.id
        WHERE team_members.user_id = ?
        ORDER BY projects.updated_at DESC
        """,
        (user[0],)
    ).fetchall()

    db.close()

    return {
        "projects": [
            {
                "id": row[0],
                "team_id": row[1],
                "team_name": row[2],
                "track_id": row[3],
                "track_name": row[4],
                "title": row[5],
                "summary": row[6],
                "repo_url": row[7],
                "status": row[8],
                "submitted_at": row[9],
                "updated_at": row[10]
            }
            for row in projects
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

@app.post("/api/events/<event_id>/voting-window")
def create_voting_window(event_id):
    user, error = require_role("organizer")

    if error:
        return error

    data = request.get_json()

    if data is None:
        return "JSON body required", 400

    starts_at = data.get("starts_at")
    ends_at = data.get("ends_at")

    if not starts_at or not ends_at:
        return "Voting window dates are required", 400

    try:
        starts = datetime.fromisoformat(
            starts_at.replace("Z", "+00:00")
        )

        ends = datetime.fromisoformat(
            ends_at.replace("Z", "+00:00")
        )
    except ValueError:
        return "Invalid voting window date format", 400

    if ends <= starts:
        return "Voting end time must be after start time", 400

    db = get_db()

    event = db.execute(
        """
        SELECT 1
        FROM events
        WHERE id = ?
        """,
        (event_id,)
    ).fetchone()

    if event is None:
        db.close()
        return "Event not found", 404

    voting_window_id = db.execute(
        """
        INSERT INTO voting_windows
        (event_id, starts_at, ends_at)
        VALUES (?, ?, ?)
        """,
        (
            event_id,
            starts_at,
            ends_at
        )
    ).lastrowid

    db.commit()
    db.close()

    return {
        "message": "Voting window created",
        "voting_window_id": voting_window_id,
        "event_id": event_id,
        "starts_at": starts_at,
        "ends_at": ends_at
    }, 201

@app.post("/api/events/<event_id>/voter-token")
def create_voter_token(event_id):
    user, error = require_role("organizer")

    if error:
        return error

    db = get_db()

    event = db.execute(
        """
        SELECT 1
        FROM events
        WHERE id = ?
        """,
        (event_id,)
    ).fetchone()

    if event is None:
        db.close()
        return "Event not found", 404

    token = str(uuid.uuid4())

    created_at = datetime.now(timezone.utc).isoformat()

    db.execute(
        """
        INSERT INTO voter_tokens
        (event_id, token, created_at)
        VALUES (?, ?, ?)
        """,
        (
            event_id,
            token,
            created_at
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Voter token created",
        "event_id": event_id,
        "token": token
    }, 201

@app.post("/api/community-vote")
def cast_community_vote():
    data = request.get_json()

    if data is None:
        return "JSON body required", 400

    event_id = data.get("event_id")
    token = data.get("token")
    project_id = data.get("project_id")

    if not event_id or not token or not project_id:
        return "event_id, token and project_id are required", 400

    now = datetime.now(timezone.utc)

    db = get_db()

    voting_window = db.execute(
        """
        SELECT id, starts_at, ends_at
        FROM voting_windows
        WHERE event_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (event_id,)
    ).fetchone()

    if voting_window is None:
        db.close()
        return "Voting window not found", 404

    try:
        starts_at = datetime.fromisoformat(
            voting_window[1].replace("Z", "+00:00")
        )
        ends_at = datetime.fromisoformat(
            voting_window[2].replace("Z", "+00:00")
        )
    except ValueError:
        db.close()
        return "Invalid voting window date format", 500

    if now < starts_at:
        db.close()
        return "Voting has not started", 403

    if now >= ends_at:
        db.close()
        return "Voting has ended", 403

    voter = db.execute(
        """
        SELECT id
        FROM voter_tokens
        WHERE event_id = ? AND token = ?
        """,
        (event_id, token)
    ).fetchone()

    if voter is None:
        db.close()
        return "Invalid voter token", 401

    project = db.execute(
        """
        SELECT projects.id
        FROM projects
        JOIN teams ON projects.team_id = teams.id
        WHERE projects.id = ? AND teams.event_id = ?
        """,
        (project_id, event_id)
    ).fetchone()

    if project is None:
        db.close()
        return "Project not found", 404

    existing_vote = db.execute(
        """
        SELECT id
        FROM community_votes
        WHERE event_id = ? AND voter_token_id = ?
        """,
        (event_id, voter[0])
    ).fetchone()

    if existing_vote is not None:
        db.close()
        return "This voter has already voted", 409

    created_at = now.isoformat()

    db.execute(
        """
        INSERT INTO community_votes
        (event_id, voter_token_id, project_id, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            event_id,
            voter[0],
            project_id,
            created_at
        )
    )

    db.execute(
        """
        UPDATE voter_tokens
        SET last_vote_at = ?
        WHERE id = ?
        """,
        (
            created_at,
            voter[0]
        )
    )

    db.execute(
        """
        INSERT INTO audit_log
        (event_id, action, voter_token_id, project_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            event_id,
            "community_vote",
            voter[0],
            project_id,
            created_at
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Vote recorded",
        "event_id": event_id,
        "project_id": project_id
    }, 201

@app.get("/api/events/<event_id>/community-results")
def get_community_results(event_id):
    db = get_db()

    voting_window = db.execute(
        """
        SELECT starts_at, ends_at
        FROM voting_windows
        WHERE event_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (event_id,)
    ).fetchone()

    if voting_window is None:
        db.close()
        return "Voting window not found", 404

    now = datetime.now(timezone.utc)

    try:
        starts_at = datetime.fromisoformat(
            voting_window[0].replace("Z", "+00:00")
        )
        ends_at = datetime.fromisoformat(
            voting_window[1].replace("Z", "+00:00")
        )
    except ValueError:
        db.close()
        return "Invalid voting window date format", 500

    if now < ends_at:
        db.close()
        return "Results are hidden during voting", 403

    results = db.execute(
        """
        SELECT
            community_votes.project_id,
            projects.title,
            COUNT(*) AS vote_count
        FROM community_votes
        JOIN projects
            ON community_votes.project_id = projects.id
        JOIN teams
            ON projects.team_id = teams.id
        WHERE community_votes.event_id = ?
          AND teams.event_id = ?
        GROUP BY community_votes.project_id, projects.title
        ORDER BY vote_count DESC
        """,
        (event_id, event_id)
    ).fetchall()

    db.close()

    return {
        "event_id": event_id,
        "results": [
            {
                "project_id": row[0],
                "title": row[1],
                "vote_count": row[2]
            }
            for row in results
        ]
    }, 200

@app.get("/api/events/<event_id>/ballot")
def get_ballot(event_id):
    token = request.args.get("token")

    if not token:
        return "Voter token is required", 401

    db = get_db()

    voter = db.execute(
        """
        SELECT id
        FROM voter_tokens
        WHERE event_id = ? AND token = ?
        """,
        (event_id, token)
    ).fetchone()

    if voter is None:
        db.close()
        return "Invalid voter token", 401

    voting_window = db.execute(
        """
        SELECT starts_at, ends_at
        FROM voting_windows
        WHERE event_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (event_id,)
    ).fetchone()

    if voting_window is None:
        db.close()
        return "Voting window not found", 404

    now = datetime.now(timezone.utc)

    try:
        starts_at = datetime.fromisoformat(
            voting_window[0].replace("Z", "+00:00")
        )
        ends_at = datetime.fromisoformat(
            voting_window[1].replace("Z", "+00:00")
        )
    except ValueError:
        db.close()
        return "Invalid voting window date format", 500

    if now < starts_at:
        db.close()
        return "Voting has not started", 403

    if now >= ends_at:
        db.close()
        return "Voting has ended", 403

    projects = db.execute(
        """
        SELECT projects.id, projects.title, projects.summary, projects.repo_url
        FROM projects
        JOIN teams ON projects.team_id = teams.id
        WHERE teams.event_id = ?
          AND projects.submitted_at IS NOT NULL
        ORDER BY RANDOM()
        """,
        (event_id,)
    ).fetchall()

    db.close()

    return {
        "event_id": event_id,
        "projects": [
            {
                "id": row[0],
                "title": row[1],
                "summary": row[2],
                "repo_url": row[3]
            }
            for row in projects
        ]
    }, 200

@app.post("/api/projects/<project_id>/comments")
def add_project_comment(project_id):
    data = request.get_json()

    if data is None:
        return "JSON body required", 400

    event_id = data.get("event_id")
    token = data.get("token")
    comment = data.get("comment")

    if not event_id or not token or not comment:
        return "event_id, token and comment are required", 400

    comment = comment.strip()

    if not comment:
        return "Comment cannot be empty", 400

    db = get_db()

    voter = db.execute(
        """
        SELECT id
        FROM voter_tokens
        WHERE event_id = ? AND token = ?
        """,
        (event_id, token)
    ).fetchone()

    if voter is None:
        db.close()
        return "Invalid voter token", 401

    recent_comments = db.execute(
        """
        SELECT COUNT(*)
        FROM audit_log
        WHERE event_id = ?
          AND voter_token_id = ?
          AND action = 'project_comment'
          AND created_at >= datetime('now', '-10 minutes')
        """,
        (event_id, voter[0])
    ).fetchone()[0]

    if recent_comments >= 5:
        db.close()
        return "Comment rate limit exceeded", 429

    project = db.execute(
        """
        SELECT projects.id
        FROM projects
        JOIN teams ON projects.team_id = teams.id
        WHERE projects.id = ? AND teams.event_id = ?
        """,
        (project_id, event_id)
    ).fetchone()

    if project is None:
        db.close()
        return "Project not found", 404

    created_at = datetime.now(timezone.utc).isoformat()

    comment_id = db.execute(
        """
        INSERT INTO project_comments
        (project_id, voter_token_id, comment, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            project_id,
            voter[0],
            comment,
            created_at
        )
    ).lastrowid

    db.execute(
        """
        INSERT INTO audit_log
        (event_id, action, voter_token_id, project_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            event_id,
            "project_comment",
            voter[0],
            project_id,
            created_at
        )
    )

    db.commit()
    db.close()

    return {
        "message": "Comment added",
        "comment_id": comment_id,
        "project_id": project_id
    }, 201

@app.get("/api/projects/<project_id>/comments")
def get_project_comments(project_id):
    db = get_db()

    project = db.execute(
        """
        SELECT projects.id
        FROM projects
        WHERE projects.id = ?
        """,
        (project_id,)
    ).fetchone()

    if project is None:
        db.close()
        return "Project not found", 404

    comments = db.execute(
        """
        SELECT
            project_comments.id,
            project_comments.comment,
            project_comments.created_at
        FROM project_comments
        WHERE project_comments.project_id = ?
        ORDER BY project_comments.created_at ASC
        """,
        (project_id,)
    ).fetchall()

    db.close()

    return {
        "project_id": project_id,
        "comments": [
            {
                "id": row[0],
                "comment": row[1],
                "created_at": row[2]
            }
            for row in comments
        ]
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

@app.get("/api/events/<event_id>/rubric")
def get_rubric(event_id):
    user, error = require_role("judge")

    if error:
        return error

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

    criteria = db.execute(
        """
        SELECT id, name, weight
        FROM rubric_criteria
        WHERE event_id = ?
        ORDER BY id
        """,
        (event_id,)
    ).fetchall()

    db.close()

    return {
        "event_id": event_id,
        "criteria": [
            {
                "id": row[0],
                "name": row[1],
                "weight": row[2]
            }
            for row in criteria
        ]
    }, 200

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
seed_rubric()
seed_tracks()
seed_teams()
seed_team_members()
seed_projects()
seed_scores()
seed_assignments()
seed_demo_sessions()

@app.get("/")
def home():
    db = get_db()

    event = db.execute(
        "SELECT id FROM events ORDER BY id LIMIT 1"
    ).fetchone()

    db.close()

    event_id = event[0] if event else ""

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dogfood 2026</title>

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

            .hero {
                background: white;
                border-radius: 10px;
                padding: 48px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                margin-bottom: 32px;
            }

            h1 {
                margin: 0 0 8px;
                font-size: 42px;
            }

            .subtitle {
                color: #6b7280;
                font-size: 18px;
                margin: 0 0 28px;
            }

            .buttons {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }

            .button {
                display: inline-block;
                padding: 12px 18px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
                font-size: 14px;
            }

            .primary {
                background: #2563eb;
                color: white;
            }

            .secondary {
                background: #e5e7eb;
                color: #1f2937;
            }

            .section-title {
                margin-bottom: 16px;
            }

            .cards {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
            }

            .card {
                background: white;
                border-radius: 10px;
                padding: 24px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }

            .card h3 {
                margin-top: 0;
                margin-bottom: 8px;
            }

            .card p {
                color: #6b7280;
                line-height: 1.5;
                margin-bottom: 18px;
            }

            .card a {
                color: #2563eb;
                text-decoration: none;
                font-weight: bold;
                font-size: 14px;
            }

            @media (max-width: 800px) {
                .cards {
                    grid-template-columns: 1fr;
                }

                .hero {
                    padding: 32px;
                }

                h1 {
                    font-size: 34px;
                }
            }

            @media (max-width: 500px) {
                .container {
                    padding: 24px 16px;
                }

                .hero {
                    padding: 24px;
                }
            }
        </style>
    </head>

    <body>
        <div class="container">

            <section class="hero">
                <h1>Dogfood 2026 🐺</h1>
                <p class="subtitle">
                    A self-hostable hackathon registration, submission, judging, and results portal.
                </p>

                <div class="buttons">
                    <a class="button primary" href="/projects">View Projects</a>
                    <a class="button secondary" href="/events/""" + event_id + """/community-vote">
                        Community Voting
                    </a>
                </div>
            </section>

            <h2 class="section-title">Explore Dogfood</h2>

            <section class="cards">

                <div class="card">
                    <h3>Project Gallery</h3>
                    <p>
                        Browse submitted hackathon projects and explore what teams have built.
                    </p>
                    <a href="/projects">Open Gallery →</a>
                </div>

                <div class="card">
                    <h3>Community Voting</h3>
                    <p>
                        View the randomized ballot and cast a community vote using your voter token.
                    </p>
                    <a href="/events/""" + event_id + """/community-vote">Enter Voting →</a>
                </div>

                <div class="card">
                    <h3>Participant Access</h3>
                    <p>
                        Sign in to access participant functionality such as project submission.
                    </p>
                    <a href="/login">Sign In →</a>
                </div>

            </section>

        </div>
    </body>
    </html>
    """
    return html


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
            projects.track_id,
            teams.event_id
        FROM judge_assignments
        JOIN projects
            ON judge_assignments.project_id = projects.id
        JOIN teams
            ON projects.team_id = teams.id
        WHERE judge_assignments.judge_id = ?
        ORDER BY projects.id
        """,
        (user[0],)
    ).fetchall()

    db.close()

    event_id = rows[0][5] if rows else None

    return {
        "event_id": event_id,
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

@app.get("/login")
def login_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login — Dogfood 2026</title>

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

            .card {
                max-width: 500px;
                margin: 60px auto;
                background: white;
                border-radius: 10px;
                padding: 32px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            }

            h1 {
                margin-top: 0;
                margin-bottom: 8px;
            }

            .subtitle {
                color: #6b7280;
                margin-top: 0;
                margin-bottom: 28px;
                line-height: 1.5;
            }

            label {
                display: block;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 8px;
            }

            input {
                width: 100%;
                padding: 12px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 15px;
                margin-bottom: 16px;
            }

            input:focus {
                outline: none;
                border-color: #2563eb;
            }

            button {
                width: 100%;
                padding: 12px;
                border: none;
                border-radius: 8px;
                background: #2563eb;
                color: white;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
            }

            button:hover {
                background: #1d4ed8;
            }

            .back {
                display: inline-block;
                margin-top: 20px;
                color: #2563eb;
                text-decoration: none;
                font-size: 14px;
            }

            .demo-note {
                margin-top: 24px;
                padding: 14px;
                background: #f9fafb;
                border-radius: 8px;
                color: #6b7280;
                font-size: 13px;
                line-height: 1.5;
            }

            @media (max-width: 500px) {
                .container {
                    padding: 24px 16px;
                }

                .card {
                    margin: 24px auto;
                    padding: 24px;
                }
            }
        </style>
    </head>

    <body>
        <div class="container">
            <div class="card">
                <h1>Sign in</h1>

                <p class="subtitle">
                    Access your Dogfood portal account.
                </p>

                <form method="POST" action="/login">
                    <label for="email">Email</label>

                    <input
                        type="email"
                        id="email"
                        name="email"
                        placeholder="you@example.com"
                        required
                    >

                    <button type="submit">Sign in</button>
                </form>

                <div class="demo-note">
                    Demo authentication uses the seeded user accounts.
                </div>

                <a class="back" href="/">← Back to Dogfood</a>
            </div>
        </div>
    </body>
    </html>
    """

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

    response = redirect("/portal")
    response.set_cookie("session", session_id)
    return response

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
