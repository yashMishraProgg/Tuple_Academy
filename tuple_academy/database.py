"""
database.py — SQLite setup using sqlite3 directly (no ORM needed for simplicity).
All schema DDL lives here. Call init_db(app) once at startup.
"""

import sqlite3
import os
from flask import g


def get_db(app=None):
    """Get a DB connection. Uses Flask's g object inside request context."""
    if 'db' not in g:
        from flask import current_app
        cfg = app.config if app else current_app.config
        g.db = sqlite3.connect(
            cfg['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row  # rows behave like dicts
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    """Create all tables if they don't exist."""
    app.teardown_appcontext(close_db)

    db_path = app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    schema = """
    -- ─── USERS ────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        email       TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,
        college     TEXT,
        course      TEXT,
        year        TEXT,
        phone       TEXT,
        linkedin    TEXT,
        github      TEXT,
        bio         TEXT,
        avatar_url  TEXT,
        role        TEXT NOT NULL DEFAULT 'student',  -- student | admin
        is_verified INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- ─── INTERNSHIPS ──────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS internships (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        title           TEXT NOT NULL,
        domain          TEXT NOT NULL,
        description     TEXT,
        duration_weeks  INTEGER NOT NULL DEFAULT 4,
        difficulty      TEXT NOT NULL DEFAULT 'Beginner',  -- Beginner|Intermediate|Advanced
        category        TEXT NOT NULL DEFAULT 'tech',      -- tech|design|business|marketing
        skills_learned  TEXT,   -- JSON array string
        total_tasks     INTEGER NOT NULL DEFAULT 12,
        is_active       INTEGER NOT NULL DEFAULT 1,
        seats_available INTEGER NOT NULL DEFAULT 200,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- ─── APPLICATIONS ─────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS applications (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        internship_id   INTEGER NOT NULL REFERENCES internships(id),
        motivation      TEXT,
        status          TEXT NOT NULL DEFAULT 'pending',  -- pending|accepted|rejected|withdrawn
        plan            TEXT NOT NULL DEFAULT 'free',     -- free|professional|pro
        payment_id      TEXT,
        offer_sent      INTEGER NOT NULL DEFAULT 0,
        start_date      TEXT,
        end_date        TEXT,
        applied_at      TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(user_id, internship_id)
    );

    -- ─── TASKS ────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS tasks (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        internship_id   INTEGER NOT NULL REFERENCES internships(id),
        week_number     INTEGER NOT NULL,
        title           TEXT NOT NULL,
        description     TEXT NOT NULL,
        instructions    TEXT,
        resources       TEXT,   -- JSON array of links
        submission_type TEXT NOT NULL DEFAULT 'link',  -- link|file|text|github
        max_score       INTEGER NOT NULL DEFAULT 100,
        deadline_days   INTEGER NOT NULL DEFAULT 7,    -- days from week start
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- ─── SUBMISSIONS ──────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS submissions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id         INTEGER NOT NULL REFERENCES tasks(id),
        application_id  INTEGER NOT NULL REFERENCES applications(id),
        user_id         INTEGER NOT NULL REFERENCES users(id),
        submission_url  TEXT,
        submission_text TEXT,
        submission_file TEXT,
        score           INTEGER,
        feedback        TEXT,
        status          TEXT NOT NULL DEFAULT 'submitted',  -- submitted|reviewed|late|rejected
        submitted_at    TEXT NOT NULL DEFAULT (datetime('now')),
        reviewed_at     TEXT,
        UNIQUE(task_id, user_id)
    );

    -- ─── CERTIFICATES ─────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS certificates (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        cert_id         TEXT UNIQUE NOT NULL,
        user_id         INTEGER NOT NULL REFERENCES users(id),
        application_id  INTEGER NOT NULL REFERENCES applications(id),
        internship_id   INTEGER NOT NULL REFERENCES internships(id),
        final_score     INTEGER NOT NULL,
        grade           TEXT NOT NULL,  -- A|B|C|Pass
        pdf_path        TEXT,
        qr_path         TEXT,
        issued_at       TEXT NOT NULL DEFAULT (datetime('now')),
        is_revoked      INTEGER NOT NULL DEFAULT 0,
        revoke_reason   TEXT
    );

    -- ─── NOTIFICATIONS ────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS notifications (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id),
        title       TEXT NOT NULL,
        message     TEXT NOT NULL,
        type        TEXT NOT NULL DEFAULT 'info',  -- info|success|warning|error
        is_read     INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    -- ─── Seed internships if empty ────────────────────────────────────────────
    INSERT OR IGNORE INTO internships (id, title, domain, description, duration_weeks, difficulty, category, skills_learned, total_tasks)
    VALUES
    (1,  'Web Development',        'web_dev',      'Build real websites with HTML, CSS, JS and React. Deploy live projects.',       4, 'Beginner',     'tech',      '["HTML5","CSS3","JavaScript","React","Git","Netlify"]', 12),
    (2,  'AI / Machine Learning',  'ai_ml',        'Work with Python, Pandas and Scikit-learn. Build and deploy ML models.',        6, 'Intermediate', 'tech',      '["Python","NumPy","Pandas","Scikit-learn","Streamlit"]', 18),
    (3,  'Data Science',           'data_science', 'Clean datasets, build visualizations and write data-driven reports.',          4, 'Beginner',     'tech',      '["Python","Pandas","Power BI","SQL","Seaborn"]', 14),
    (4,  'UI/UX Design',           'uiux',         'Learn Figma, design real app screens and build a UX case study.',              4, 'Beginner',     'design',    '["Figma","Wireframing","Prototyping","User Research"]', 10),
    (5,  'Cybersecurity',          'cybersec',     'Study OWASP Top 10, basic ethical hacking and write audit reports.',           4, 'Intermediate', 'tech',      '["Linux","Burp Suite","OWASP","Pen Testing"]', 12),
    (6,  'Digital Marketing',      'dig_mktg',     'Create content calendars, run mock Meta Ads and write strategy reports.',      4, 'Beginner',     'marketing', '["SEO","Google Analytics","Meta Ads","Canva"]', 12),
    (7,  'Content Writing',        'content',      'Write SEO blogs, social copy and publish a portfolio piece on Medium.',        3, 'Beginner',     'business',  '["SEO Writing","Copywriting","Grammarly","Research"]', 9),
    (8,  'Cloud Computing',        'cloud',        'AWS fundamentals, deploy apps and manage cloud infrastructure basics.',        4, 'Intermediate', 'tech',      '["AWS","EC2","S3","Lambda","IAM"]', 12),
    (9,  'Python Programming',     'python',       'Build automation scripts, scrapers and a Telegram bot using Python.',         4, 'Beginner',     'tech',      '["Python","OOP","BeautifulSoup","APIs","Automation"]', 12),
    (10, 'App Development',        'app_dev',      'Build cross-platform mobile apps with Flutter or React Native.',              6, 'Intermediate', 'tech',      '["Flutter","Dart","React Native","REST APIs"]', 16),
    (11, 'Graphic Design',         'graphic',      'Create brand identities, social media posts and marketing materials.',        3, 'Beginner',     'design',    '["Canva","Adobe Illustrator","Typography","Branding"]', 9),
    (12, 'Video Editing',          'video',        'Edit promotional videos, reels and YouTube content using professional tools.',3, 'Beginner',     'design',    '["Premiere Pro","DaVinci Resolve","Motion Graphics"]', 9),
    (13, 'Finance',                'finance',      'Financial analysis, Excel modelling, investment basics and report writing.',  4, 'Beginner',     'business',  '["Excel","Financial Modelling","Ratio Analysis"]', 10),
    (14, 'Business Development',   'biz_dev',      'Market research, cold outreach, pitch decks and BD strategy frameworks.',    4, 'Beginner',     'business',  '["Market Research","CRM","Pitch Decks","Outreach"]', 10),
    (15, 'HR Management',          'hr',           'JD writing, resume screening, interview frameworks and HR policy drafting.',  3, 'Beginner',     'business',  '["JD Writing","Screening","HRMS","Policy Drafting"]', 9),
    (16, 'Java Development',       'java',         'Core Java, OOP, JDBC and building a console-based application project.',     4, 'Intermediate', 'tech',      '["Java","OOP","JDBC","Collections","Spring Basics"]', 12),
    (17, 'DevOps',                 'devops',       'CI/CD pipelines, Docker, GitHub Actions and deployment automation.',         4, 'Advanced',     'tech',      '["Docker","GitHub Actions","CI/CD","Linux","Nginx"]', 14),
    (18, 'Blockchain',             'blockchain',   'Solidity basics, smart contracts and deploying on a test network.',          4, 'Advanced',     'tech',      '["Solidity","Web3.js","Truffle","MetaMask","Polygon"]', 12);
    """

    conn.executescript(schema)
    conn.commit()
    conn.close()
    print("✅ Database initialized: tuple_academy.db")
