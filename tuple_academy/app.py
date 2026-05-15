"""
Tuple Academy — Flask Backend
Complete backend: auth, internships, applications, admin panel.
Run: python app.py
"""
import sqlite3, hashlib, uuid, os, secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, request, jsonify, g, session,
    render_template, redirect, url_for
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "tuple-academy-dev-secret-2025")

# ── DATABASE PATH ─────────────────────────────────────────────
# On Render (and most cloud hosts) the project directory is read-only.
# We use /tmp for the DB when running in production (RENDER env var is set
# automatically by Render). Locally we use instance/ as before.
if os.environ.get("RENDER"):
    _db_dir = "/tmp"
else:
    _db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")

app.config["DATABASE"]      = os.path.join(_db_dir, "tuple.db")
app.config["UPLOAD_FOLDER"] = os.path.join(_db_dir, "uploads")
app.permanent_session_lifetime = timedelta(days=7)

# ── DB ────────────────────────────────────────────────────────
# Track whether this process has already set up the schema
_schema_created = False

def _ensure_schema(db):
    """Create all tables + seed data if not already done in this process."""
    global _schema_created
    if _schema_created:
        return
    _schema_created = True
    # Make upload dir
    try:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id         TEXT PRIMARY KEY,
        name       TEXT NOT NULL,
        email      TEXT UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        college    TEXT DEFAULT \'\',
        stream     TEXT DEFAULT \'\',
        phone      TEXT DEFAULT \'\',
        role       TEXT DEFAULT \'student\',
        is_active  INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime(\'now\'))
    );
    CREATE TABLE IF NOT EXISTS internships (
        id             TEXT PRIMARY KEY,
        title          TEXT NOT NULL,
        category       TEXT DEFAULT \'tech\',
        description    TEXT DEFAULT \'\',
        duration_weeks INTEGER DEFAULT 4,
        difficulty     TEXT DEFAULT \'Beginner\',
        skills         TEXT DEFAULT \'\',
        is_active      INTEGER DEFAULT 1,
        enrolled       INTEGER DEFAULT 0,
        created_at     TEXT DEFAULT (datetime(\'now\'))
    );
    CREATE TABLE IF NOT EXISTS applications (
        id            TEXT PRIMARY KEY,
        user_id       TEXT NOT NULL,
        internship_id TEXT NOT NULL,
        status        TEXT DEFAULT \'pending\',
        motivation    TEXT DEFAULT \'\',
        start_date    TEXT DEFAULT \'\',
        end_date      TEXT DEFAULT \'\',
        score         INTEGER DEFAULT 0,
        applied_at    TEXT DEFAULT (datetime(\'now\')),
        UNIQUE(user_id, internship_id),
        FOREIGN KEY(user_id)       REFERENCES users(id),
        FOREIGN KEY(internship_id) REFERENCES internships(id)
    );
    CREATE TABLE IF NOT EXISTS certificates (
        id        TEXT PRIMARY KEY,
        cert_id   TEXT UNIQUE NOT NULL,
        user_id   TEXT NOT NULL,
        app_id    TEXT NOT NULL,
        issued_at TEXT DEFAULT (datetime(\'now\')),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(app_id)  REFERENCES applications(id)
    );
    CREATE TABLE IF NOT EXISTS contacts (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        email      TEXT NOT NULL,
        phone      TEXT DEFAULT \'\',
        subject    TEXT DEFAULT \'\',
        message    TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime(\'now\'))
    );
    """)
    db.commit()
    _seed(db)

def _seed(db):
    import random
    # Admin
    if not db.execute("SELECT id FROM users WHERE email=?", ("admin@tupleacademy.in",)).fetchone():
        db.execute("INSERT INTO users(id,name,email,password,role) VALUES(?,?,?,?,?)",
            (str(uuid.uuid4()), "Admin", "admin@tupleacademy.in", _hp("admin123"), "admin"))
        db.commit()
    # Demo student
    if not db.execute("SELECT id FROM users WHERE email=?", ("student@example.com",)).fetchone():
        db.execute("INSERT INTO users(id,name,email,password,college,stream) VALUES(?,?,?,?,?,?)",
            (str(uuid.uuid4()), "Priya Sharma", "student@example.com", _hp("student123"), "Delhi University", "CSE"))
        db.commit()
    # Internships
    if not db.execute("SELECT id FROM internships LIMIT 1").fetchone():
        programs = [
            ("Web Development","tech","Build real websites with HTML, CSS, JS & React. Deploy live projects.",4,"Beginner","HTML,CSS,JavaScript,React,Git",2400),
            ("AI / Machine Learning","tech","Python, Pandas, Scikit-learn. Build prediction models & Streamlit apps.",6,"Intermediate","Python,Pandas,Scikit-learn,TensorFlow",1800),
            ("Data Science","tech","Clean datasets, build dashboards with Python & Power BI.",4,"Beginner","Python,Pandas,SQL,Power BI",1600),
            ("Cybersecurity","tech","OWASP Top 10, ethical hacking basics, security audit reports.",4,"Intermediate","Kali Linux,Burp Suite,Networking",1200),
            ("UI/UX Design","design","Figma, wireframes, real app screens, UX case study.",4,"Beginner","Figma,Wireframing,Prototyping",900),
            ("Graphic Design","design","Brand identities, social media assets, print-ready designs.",3,"Beginner","Canva,Illustrator,Typography",800),
            ("Digital Marketing","marketing","SEO, Meta Ads, content calendars, full strategy report.",4,"Beginner","SEO,Google Analytics,Meta Ads",1100),
            ("Content Writing","marketing","SEO blogs, ad copy, product descriptions, Medium portfolio.",3,"Beginner","SEO Writing,Copywriting,Grammarly",780),
            ("Python Programming","tech","OOP, automation, web scraping, Telegram bot.",4,"Beginner","Python,OOP,BeautifulSoup,APIs",1350),
            ("App Development","tech","Flutter/React Native. Full CRUD mobile app.",6,"Intermediate","Flutter,Dart,React Native",670),
            ("Cloud Computing","tech","AWS/GCP, EC2, S3, Lambda. Full cloud deployment.",4,"Intermediate","AWS,EC2,S3,Lambda",540),
            ("DevOps","tech","Docker, GitHub Actions, CI/CD pipelines.",4,"Intermediate","Docker,GitHub Actions,CI/CD",480),
            ("Finance","business","Financial modelling, Excel dashboards, investment reports.",4,"Beginner","Excel,Financial Modelling,Python",420),
            ("HR Management","business","Recruitment, JDs, HR policies, employee engagement.",3,"Beginner","Recruitment,HR Policies,Excel",390),
            ("Business Development","business","Lead gen, pitch decks, market research, sales strategy.",4,"Beginner","Sales,Market Research,PowerPoint",460),
            ("Video Editing","design","DaVinci Resolve/Premiere. Real briefs, polished showreel.",4,"Beginner","DaVinci Resolve,Premiere Pro,Color Grading",350),
            ("Java Development","tech","Core Java, Spring Boot, REST APIs, mini-project.",6,"Intermediate","Java,Spring Boot,Maven,REST API",520),
            ("Blockchain","tech","Ethereum, Solidity smart contracts, testnet deployment.",6,"Advanced","Solidity,Ethereum,Web3.js,Truffle",280),
        ]
        for p in programs:
            db.execute("INSERT INTO internships(id,title,category,description,duration_weeks,difficulty,skills,enrolled) VALUES(?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), p[0], p[1], p[2], p[3], p[4], p[5], p[6]))
        db.commit()

def get_db():
    if "db" not in g:
        db_path = app.config["DATABASE"]
        # Ensure parent dir exists (safe for both /tmp and instance/)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except OSError:
                pass
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
        # Always ensure schema exists — safe to call every new connection
        _ensure_schema(g.db)
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db: db.close()

def qry(sql, p=(), one=False, commit=False):
    db = get_db()
    cur = db.execute(sql, p)
    if commit:
        db.commit()
        return cur.lastrowid
    return cur.fetchone() if one else cur.fetchall()

def rows(sql, p=()):
    return [dict(r) for r in qry(sql, p)]

def row(sql, p=()):
    r = qry(sql, p, one=True)
    return dict(r) if r else None

def _hp(pw): return hashlib.sha256(pw.encode()).hexdigest()

# ── AUTH HELPERS ──────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def d(*a, **kw):
        if "user_id" not in session:
            if request.is_json: return jsonify(ok=False, error="Not logged in"), 401
            return redirect(url_for("login_page"))
        return f(*a, **kw)
    return d

def admin_required(f):
    @wraps(f)
    def d(*a, **kw):
        if session.get("role") != "admin":
            if request.is_json: return jsonify(ok=False, error="Admin only"), 403
            return redirect(url_for("index"))
        return f(*a, **kw)
    return d

def me():
    uid = session.get("user_id")
    return row("SELECT * FROM users WHERE id=?", (uid,)) if uid else None

# ── PAGE ROUTES ───────────────────────────────────────────────
@app.route("/")
def index():
    interns = rows("SELECT * FROM internships WHERE is_active=1 ORDER BY enrolled DESC LIMIT 8")
    stats = {
        "students":     qry("SELECT COUNT(*) FROM users WHERE role='student'", one=True)[0],
        "internships":  qry("SELECT COUNT(*) FROM internships WHERE is_active=1", one=True)[0],
        "certificates": qry("SELECT COUNT(*) FROM certificates", one=True)[0],
        "applications": qry("SELECT COUNT(*) FROM applications", one=True)[0],
    }
    return render_template("index.html", internships=interns, stats=stats, user=me())

@app.route("/internships")
def internships_page():
    cat = request.args.get("cat", "all")
    q = "SELECT * FROM internships WHERE is_active=1"
    p = ()
    if cat != "all":
        q += " AND category=?"
        p = (cat,)
    q += " ORDER BY enrolled DESC"
    return render_template("internships.html", internships=rows(q, p), active_cat=cat, user=me())

@app.route("/internship/<iid>")
def internship_detail(iid):
    intern = row("SELECT * FROM internships WHERE id=?", (iid,))
    if not intern: return "Not found", 404
    already = None
    if session.get("user_id"):
        already = row("SELECT * FROM applications WHERE user_id=? AND internship_id=?",
                      (session["user_id"], iid))
    return render_template("internship_detail.html", intern=intern, already=already, user=me())

@app.route("/about")
def about_page():
    return render_template("about.html", user=me())

@app.route("/contact")
def contact_page():
    return render_template("contact.html", user=me())

@app.route("/verify")
def verify_page():
    cert_id = request.args.get("id", "")
    cert = None
    if cert_id:
        cert = row("""SELECT c.cert_id, u.name as student_name, i.title as internship_title,
                             a.score, a.start_date, a.end_date, c.issued_at
                      FROM certificates c
                      JOIN users u ON u.id=c.user_id
                      JOIN applications a ON a.id=c.app_id
                      JOIN internships i ON i.id=a.internship_id
                      WHERE c.cert_id=?""", (cert_id,))
    return render_template("verify.html", cert=cert, cert_id=cert_id, user=me())

@app.route("/login")
def login_page():
    if "user_id" in session: return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register")
def register_page():
    if "user_id" in session: return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    apps = rows("""SELECT a.*, i.title, i.category, i.duration_weeks, i.difficulty
                   FROM applications a JOIN internships i ON i.id=a.internship_id
                   WHERE a.user_id=? ORDER BY a.applied_at DESC""", (uid,))
    certs = rows("""SELECT c.*, i.title, i.category
                    FROM certificates c
                    JOIN applications a ON a.id=c.app_id
                    JOIN internships i ON i.id=a.internship_id
                    WHERE c.user_id=?""", (uid,))
    return render_template("dashboard.html", user=me(), applications=apps, certificates=certs)

@app.route("/admin")
@login_required
@admin_required
def admin_panel():
    users_   = rows("SELECT * FROM users ORDER BY created_at DESC")
    interns_ = rows("SELECT * FROM internships ORDER BY created_at DESC")
    apps_    = rows("""SELECT a.*, u.name as student_name, u.email as student_email, i.title as intern_title
                       FROM applications a JOIN users u ON u.id=a.user_id
                       JOIN internships i ON i.id=a.internship_id ORDER BY a.applied_at DESC""")
    contacts_= rows("SELECT * FROM contacts ORDER BY created_at DESC LIMIT 50")
    certs_   = rows("""SELECT c.*, u.name, i.title FROM certificates c
                       JOIN users u ON u.id=c.user_id JOIN applications a ON a.id=c.app_id
                       JOIN internships i ON i.id=a.internship_id ORDER BY c.issued_at DESC""")
    stats = {
        "total_users": len([u for u in users_ if u["role"]=="student"]),
        "total_apps":  len(apps_),
        "total_certs": len(certs_),
        "pending":     len([a for a in apps_ if a["status"]=="pending"]),
    }
    return render_template("admin.html", users=users_, internships=interns_,
                           applications=apps_, contacts=contacts_, certificates=certs_,
                           stats=stats, user=me())

# ── API ───────────────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def api_register():
    d = request.get_json(silent=True) or request.form
    name, email, pw = (d.get("name","")).strip(), (d.get("email","")).strip().lower(), d.get("password","")
    if not name or not email or not pw:
        return jsonify(ok=False, error="Name, email and password required"), 400
    if len(pw) < 6:
        return jsonify(ok=False, error="Password min 6 characters"), 400
    if row("SELECT id FROM users WHERE email=?", (email,)):
        return jsonify(ok=False, error="Email already registered"), 409
    uid = str(uuid.uuid4())
    qry("INSERT INTO users(id,name,email,password,college,stream,phone) VALUES(?,?,?,?,?,?,?)",
        (uid, name, email, _hp(pw), d.get("college",""), d.get("stream",""), d.get("phone","")), commit=True)
    session.permanent = True
    session["user_id"] = uid
    session["role"] = "student"
    return jsonify(ok=True, message="Account created!", redirect="/dashboard")

@app.route("/api/login", methods=["POST"])
def api_login():
    d = request.get_json(silent=True) or request.form
    email, pw = (d.get("email","")).strip().lower(), d.get("password","")
    u = row("SELECT * FROM users WHERE email=?", (email,))
    if not u or u["password"] != _hp(pw):
        return jsonify(ok=False, error="Invalid email or password"), 401
    if not u["is_active"]:
        return jsonify(ok=False, error="Account deactivated"), 403
    session.permanent = True
    session["user_id"] = u["id"]
    session["role"] = u["role"]
    return jsonify(ok=True, redirect="/admin" if u["role"]=="admin" else "/dashboard")

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify(ok=True, redirect="/")

@app.route("/api/apply", methods=["POST"])
def api_apply():
    d = request.get_json(silent=True) or request.form
    uid = session.get("user_id")
    if not uid:
        name, email = (d.get("name","")).strip(), (d.get("email","")).strip().lower()
        if not name or not email:
            return jsonify(ok=False, error="Name and email required"), 400
        existing = row("SELECT id FROM users WHERE email=?", (email,))
        if existing:
            uid = existing["id"]
        else:
            uid = str(uuid.uuid4())
            qry("INSERT INTO users(id,name,email,password,college,stream,phone) VALUES(?,?,?,?,?,?,?)",
                (uid, name, email, _hp(secrets.token_hex(8)),
                 d.get("college",""), d.get("stream",""), d.get("phone","")), commit=True)
        session.permanent = True
        session["user_id"] = uid
        session["role"] = "student"

    iid = d.get("internship_id","")
    intern = row("SELECT * FROM internships WHERE id=? AND is_active=1", (iid,))
    if not intern:
        return jsonify(ok=False, error="Internship not found"), 404
    if row("SELECT id FROM applications WHERE user_id=? AND internship_id=?", (uid, iid)):
        return jsonify(ok=False, error="Already applied"), 409

    aid = str(uuid.uuid4())
    start = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    end   = (datetime.now() + timedelta(weeks=intern["duration_weeks"]+1, days=2)).strftime("%Y-%m-%d")
    qry("INSERT INTO applications(id,user_id,internship_id,status,motivation,start_date,end_date) VALUES(?,?,?,?,?,?,?)",
        (aid, uid, iid, "accepted", d.get("motivation",""), start, end), commit=True)
    qry("UPDATE internships SET enrolled=enrolled+1 WHERE id=?", (iid,), commit=True)
    return jsonify(ok=True, message="Application accepted! Check your dashboard.", redirect="/dashboard")

@app.route("/api/contact", methods=["POST"])
def api_contact():
    d = request.get_json(silent=True) or request.form
    name, email, message = (d.get("name","")).strip(), (d.get("email","")).strip(), (d.get("message","")).strip()
    if not name or not email or not message:
        return jsonify(ok=False, error="Name, email and message required"), 400
    qry("INSERT INTO contacts(name,email,phone,subject,message) VALUES(?,?,?,?,?)",
        (name, email, d.get("phone",""), d.get("subject",""), message), commit=True)
    return jsonify(ok=True, message="Message received! We'll reply within 24 hours.")

@app.route("/api/verify/<cert_id>")
def api_verify(cert_id):
    r = row("""SELECT c.cert_id, u.name as student_name, i.title as internship,
                      a.score, a.start_date, a.end_date, c.issued_at
               FROM certificates c JOIN users u ON u.id=c.user_id
               JOIN applications a ON a.id=c.app_id
               JOIN internships i ON i.id=a.internship_id WHERE c.cert_id=?""", (cert_id,))
    if not r: return jsonify(valid=False, error="Certificate not found")
    return jsonify(valid=True, **r)

# ── ADMIN API ─────────────────────────────────────────────────
@app.route("/api/admin/application/<aid>", methods=["POST"])
@login_required
@admin_required
def admin_update_app(aid):
    d = request.get_json(silent=True) or request.form
    if d.get("status"):
        qry("UPDATE applications SET status=? WHERE id=?", (d["status"], aid), commit=True)
    if d.get("score") is not None:
        sc = int(d["score"])
        qry("UPDATE applications SET score=? WHERE id=?", (sc, aid), commit=True)
        if sc >= 60: _issue_cert(aid)
    return jsonify(ok=True)

@app.route("/api/admin/application/<aid>/cert", methods=["POST"])
@login_required
@admin_required
def admin_issue_cert_route(aid):
    _issue_cert(aid)
    return jsonify(ok=True, message="Certificate issued")

def _issue_cert(app_id):
    a = row("SELECT * FROM applications WHERE id=?", (app_id,))
    if not a or row("SELECT id FROM certificates WHERE app_id=?", (app_id,)): return
    intern = row("SELECT title FROM internships WHERE id=?", (a["internship_id"],))
    code = (intern["title"][:2] if intern else "GN").upper()
    seq  = qry("SELECT COUNT(*) FROM certificates", one=True)[0] + 1
    cert_id = f"TA-{datetime.now().year}-{code}-{seq:04d}"
    qry("INSERT INTO certificates(id,cert_id,user_id,app_id) VALUES(?,?,?,?)",
        (str(uuid.uuid4()), cert_id, a["user_id"], app_id), commit=True)
    qry("UPDATE applications SET status='completed' WHERE id=?", (app_id,), commit=True)

@app.route("/api/admin/internship", methods=["POST"])
@login_required
@admin_required
def admin_add_internship():
    d = request.get_json(silent=True) or request.form
    iid = str(uuid.uuid4())
    qry("INSERT INTO internships(id,title,category,description,duration_weeks,difficulty,skills) VALUES(?,?,?,?,?,?,?)",
        (iid, d.get("title",""), d.get("category","tech"), d.get("description",""),
         int(d.get("duration_weeks",4)), d.get("difficulty","Beginner"), d.get("skills","")), commit=True)
    return jsonify(ok=True, message="Internship added", id=iid)

@app.route("/api/admin/internship/<iid>", methods=["DELETE"])
@login_required
@admin_required
def admin_del_internship(iid):
    qry("UPDATE internships SET is_active=0 WHERE id=?", (iid,), commit=True)
    return jsonify(ok=True)

@app.route("/api/admin/user/<uid>/toggle", methods=["POST"])
@login_required
@admin_required
def admin_toggle_user(uid):
    u = row("SELECT is_active FROM users WHERE id=?", (uid,))
    if u: qry("UPDATE users SET is_active=? WHERE id=?", (0 if u["is_active"] else 1, uid), commit=True)
    return jsonify(ok=True)

if __name__ == "__main__":
    with app.app_context():
        init_db()
    print("\n  ✦  Tuple Academy → http://localhost:5000")
    print("  ✦  Admin:   admin@tupleacademy.in  /  admin123")
    print("  ✦  Student: student@example.com    /  student123\n")
    app.run(debug=True, port=5000)