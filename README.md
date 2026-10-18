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
- Optional CSRF protection via Flask-WTF; it is included in requirements.
- SQLite schema upgrade routine adds new fields to existing SQLite databases without dropping application records.

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set a strong secret key before running:

```bash
# Windows PowerShell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
# macOS/Linux
export SECRET_KEY="replace-with-a-long-random-secret"
```

Run the application:

```bash
python app.py
```

Open http://127.0.0.1:5000 and create an account. The SQLite database is created automatically. When an existing SQLite database is detected, the app adds the newly required columns while preserving current rows.

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

- Set `SECRET_KEY` to a long random secret and keep it out of source control.
- Do not enable Flask debug mode in production.
- Use HTTPS and secure cookie settings when deployed.
- Use PostgreSQL or another managed database for a production multi-user deployment.
- Email verification, password reset emails, actual push/email notifications, campus placement officer workflows, AI integrations, resume file uploads/parsing and XLSX import/export need additional service configuration and are not claimed as active features in this version.
- CSV import/export is implemented; XLSX import/export is not yet implemented.
- Browser notifications and automatic scheduled emails require a background scheduler/service and explicit user notification preferences.
