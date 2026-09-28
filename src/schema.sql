CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    submissions_open TEXT NOT NULL,
    submissions_close TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS prizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (event_id) REFERENCES events(id)
);
CREATE TABLE IF NOT EXISTS rubric_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    name TEXT NOT NULL,
    weight REAL NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id)
);
CREATE TABLE IF NOT EXISTS tracks (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id)
);
CREATE TABLE IF NOT EXISTS teams (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    event_id TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id)
);
CREATE TABLE IF NOT EXISTS team_members (
    team_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (team_id, user_id),
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS team_invites (
    id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    invited_email TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    team_id TEXT NOT NULL,
    track_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    repo_url TEXT,
    submitted_at TEXT,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (track_id) REFERENCES tracks(id)
);
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judge_id INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    functionality REAL,
    quality REAL,
    comment TEXT,
    FOREIGN KEY (judge_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
    UNIQUE (judge_id, project_id)
);
CREATE TABLE IF NOT EXISTS score_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    score_id INTEGER NOT NULL,
    criterion_id INTEGER NOT NULL,
    value REAL NOT NULL,
    UNIQUE (score_id, criterion_id),
    FOREIGN KEY (score_id) REFERENCES scores(id),
    FOREIGN KEY (criterion_id) REFERENCES rubric_criteria(id)
);
CREATE TABLE IF NOT EXISTS judge_assignments (
    judge_id INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    PRIMARY KEY (judge_id, project_id),
    FOREIGN KEY (judge_id) REFERENCES users(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
CREATE TABLE IF NOT EXISTS judge_invites (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    created_at TEXT NOT NULL,
    accepted_at TEXT
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
