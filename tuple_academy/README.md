# Tuple Academy — Flask App

A full-stack virtual internship platform built with Flask + SQLite.

## 🚀 Quick Start

```bash
# 1. Install dependencies (only Flask needed!)
pip install flask

# 2. Run the app
python app.py
```

Open http://localhost:5000

## 🔑 Demo Credentials

| Role    | Email                      | Password    |
|---------|----------------------------|-------------|
| Admin   | admin@tupleacademy.in      | admin123    |
| Student | student@example.com        | student123  |

## 📁 Project Structure

```
tuple_academy/
├── app.py                  ← Flask backend (all routes + API)
├── requirements.txt
├── instance/
│   └── tuple.db            ← SQLite database (auto-created)
├── static/
│   └── uploads/            ← File uploads
└── templates/
    ├── base.html           ← Shared layout + nav + footer
    ├── index.html          ← Homepage
    ├── internships.html    ← All internships listing
    ├── internship_detail.html ← Single internship page
    ├── login.html          ← Login page
    ├── register.html       ← Register page
    ├── dashboard.html      ← Student dashboard
    ├── admin.html          ← Admin panel
    ├── about.html          ← About us page
    ├── contact.html        ← Contact page
    └── verify.html         ← Certificate verification
```

## 🌐 Pages

| URL                        | Description                    |
|----------------------------|--------------------------------|
| /                          | Homepage with hero + internships |
| /internships               | Browse all 18 domains          |
| /internship/<id>           | Internship detail + apply      |
| /about                     | About page                     |
| /contact                   | Contact form                   |
| /verify                    | Certificate verification       |
| /login                     | Student / Admin login          |
| /register                  | New student registration       |
| /dashboard                 | Student dashboard              |
| /admin                     | Admin panel                    |

## 🔌 API Endpoints

| Method | Endpoint                              | Description              |
|--------|---------------------------------------|--------------------------|
| POST   | /api/register                         | Register new user        |
| POST   | /api/login                            | Login                    |
| POST   | /api/logout                           | Logout                   |
| POST   | /api/apply                            | Apply for internship     |
| POST   | /api/contact                          | Send contact message     |
| GET    | /api/verify/<cert_id>                 | Verify certificate (JSON)|
| POST   | /api/admin/application/<id>           | Update score/status      |
| POST   | /api/admin/application/<id>/cert      | Issue certificate        |
| POST   | /api/admin/internship                 | Add new internship       |
| DELETE | /api/admin/internship/<id>            | Deactivate internship    |
| POST   | /api/admin/user/<id>/toggle           | Enable/disable user      |

## 🛠 Tech Stack

- **Backend**: Python / Flask
- **Database**: SQLite (stdlib — no extra driver needed)
- **Auth**: Server-side sessions
- **Frontend**: Jinja2 templates + vanilla JS + Google Fonts
- **Design**: Warm rust/cream color palette matching Tuple Academy brand

## 🚢 Production Deployment

```bash
# Use gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Set environment variable for production:
```bash
export SECRET_KEY="your-strong-random-secret-key"
```
