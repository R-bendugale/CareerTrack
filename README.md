# CareerTrack — Job Application & Career Tracker

A Flask application for managing job applications, interview rounds, recruiter details, follow-ups, tasks, career goals and application analytics.

## Features

- Secure password hashing, user registration/login/logout and per-user data ownership.
- Application create/read/update/delete, archive/restore, search, filtering and sorting.
- Extra application fields: job description and URL, salary/stipend, employment type, priority, source, recruiter contacts, resume version, follow-up date and assessment deadline.
- **Dynamic “Other” inputs** on status, interview type, employment type, priority and source dropdowns. Selecting `Other` reveals a required text field so users can enter a company-specific option.
- Dashboard analytics: status counts, interview/offer conversion, six-month activity chart, weekly goals, top companies, upcoming interviews, overdue task and follow-up alerts.
- Kanban board with inline status updates.
- Application detail pages with timeline events and multiple interview rounds.
- Tasks and reminders with due dates, priorities, linked applications, completion and deletion.
- Calendar-style chronological view of applications, interviews, assessment deadlines, follow-ups and tasks.
- Profile and weekly application goal settings, light/dark theme toggle, archived application page.
- CSV import/export, mobile-responsive layouts, password change and account deletion.
- Mandatory CSRF protection on POST requests via Flask-WTF.
- SQLite schema upgrade routine adds new fields to existing SQLite databases without dropping application records.

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set a strong secret key before running. For local development, the app has a development-only fallback key. For production, set `APP_ENV=production` and provide a strong `SECRET_KEY`; the app refuses to start in production without it. Production mode also enables secure session and remember cookies, so deploy behind HTTPS.

```bash
# Windows PowerShell (local development)
$env:SECRET_KEY = "replace-with-a-long-random-secret"

# Production environment (also set this in your hosting provider)
$env:APP_ENV = "production"
$env:SECRET_KEY = "replace-with-a-long-random-secret"

# macOS/Linux
export SECRET_KEY="replace-with-a-long-random-secret"
export APP_ENV="production"  # only when deploying behind HTTPS
```

Run the application locally:

```bash
python app.py
```

For a Linux production host, use the included `Procfile` (`gunicorn app:app`). Configure `APP_ENV=production`, `SECRET_KEY`, and a persistent PostgreSQL `DATABASE_URL` in the host's environment settings. Do not commit a real `.env` file or database file.

Open http://127.0.0.1:5000 and create an account. The SQLite database is created automatically. When an existing SQLite database is detected, the app adds newly required columns while preserving current rows. The repository intentionally excludes local database files; each installation creates its own database.

## Main pages

- `/dashboard` — analytics and applications
- `/applications/add` — create an application
- `/board` — Kanban status board
- `/calendar` — chronological calendar view
- `/tasks` — tasks and due dates
- `/profile` — profile and weekly goals
- `/archive` — archived applications
- `/export.csv` — download the signed-in user's application data

## Production notes

- Set `APP_ENV=production` and `SECRET_KEY` to a long random secret; keep both environment-specific settings out of source control. Production startup fails if `SECRET_KEY` is missing.
- CSRF validation is always enabled; all POST forms include a CSRF token.
- Production session and remember cookies use `Secure`, `HttpOnly`, and `SameSite=Lax` settings. HTTPS is required for secure cookies.
- Account deletion requires the current password; changing a password signs the user out so they must authenticate again.
- CSV imports skip invalid and duplicate rows and report the number skipped. Duplicate identity is based on company, role and application date for the current account.
- Do not enable Flask debug mode in production.
- Use HTTPS and secure cookie settings when deployed.
- Use PostgreSQL or another managed database for a production multi-user deployment. PostgreSQL URLs are supported through the included Psycopg 3 driver.
- The included `Procfile` starts the app with Gunicorn on Linux-based hosts.
- Email verification, password reset emails, actual push/email notifications, campus placement officer workflows, AI integrations, resume file uploads/parsing and XLSX import/export need additional service configuration and are not claimed as active features in this version.
- CSV import/export is implemented; XLSX import/export is not yet implemented.
- Browser notifications and automatic scheduled emails require a background scheduler/service and explicit user notification preferences.
