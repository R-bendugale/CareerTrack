import csv
import io
import os
from datetime import date, datetime, timedelta
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, url_for, make_response
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case, func, or_, text
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///applications.db")
if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["REMEMBER_COOKIE_HTTPONLY"] = True

# Optional security middleware: enabled when Flask-WTF is installed.
try:
    from flask_wtf.csrf import CSRFProtect
    CSRFProtect(app)
    app.jinja_env.globals["csrf_enabled"] = True
except ImportError:
    app.jinja_env.globals["csrf_enabled"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(40), default="")
    education = db.Column(db.String(180), default="")
    skills = db.Column(db.Text, default="")
    target_role = db.Column(db.String(150), default="")
    weekly_goal = db.Column(db.Integer, default=5)
    theme = db.Column(db.String(20), default="light")
    role = db.Column(db.String(30), nullable=False, default="user")
    applications = db.relationship("Application", backref="owner", lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship("Task", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    company = db.Column(db.String(150), nullable=False)
    job_role = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), default="")
    application_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(60), nullable=False, default="Applied")
    interview_date = db.Column(db.Date, nullable=True)
    interview_type = db.Column(db.String(100), default="")
    source = db.Column(db.String(100), default="")
    notes = db.Column(db.Text, default="")
    job_description = db.Column(db.Text, default="")
    job_url = db.Column(db.String(500), default="")
    salary = db.Column(db.String(100), default="")
    employment_type = db.Column(db.String(100), default="")
    priority = db.Column(db.String(20), default="Medium")
    recruiter_name = db.Column(db.String(120), default="")
    recruiter_email = db.Column(db.String(150), default="")
    recruiter_phone = db.Column(db.String(50), default="")
    recruiter_url = db.Column(db.String(500), default="")
    follow_up_date = db.Column(db.Date, nullable=True)
    assessment_deadline = db.Column(db.Date, nullable=True)
    archived = db.Column(db.Boolean, nullable=False, default=False)
    resume_version = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, server_default=func.now())
    events = db.relationship("ApplicationEvent", backref="application", lazy=True, cascade="all, delete-orphan", order_by="ApplicationEvent.created_at.desc()")
    interviews = db.relationship("Interview", backref="application", lazy=True, cascade="all, delete-orphan", order_by="Interview.interview_date.asc()")


class ApplicationEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False, index=True)
    event_type = db.Column(db.String(80), nullable=False)
    details = db.Column(db.Text, default="")
    event_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, server_default=func.now())


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False, index=True)
    round_name = db.Column(db.String(100), default="Interview")
    interview_type = db.Column(db.String(100), default="")
    interview_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, default="")
    completed = db.Column(db.Boolean, default=False, nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, default="")
    due_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(20), default="Medium")
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    application = db.relationship("Application", backref=db.backref("tasks", lazy=True))


STATUSES = ["Applied", "Assessment", "Interview", "Offer", "Selected", "Rejected", "Withdrawn", "Other"]
INTERVIEW_TYPES = ["Technical", "HR", "Online assessment", "Managerial", "Panel", "Phone screening", "Video call", "Case study", "Group discussion", "Other"]
EMPLOYMENT_TYPES = ["Full-time", "Internship", "Part-time", "Contract", "Temporary", "Apprenticeship", "Remote", "Hybrid", "On-site", "Other"]
PRIORITIES = ["High", "Medium", "Low", "Other"]
SOURCES = ["LinkedIn", "Company website", "Campus placement", "Referral", "Naukri", "Indeed", "Internshala", "College notice", "Recruiter", "Other"]
EVENT_TYPES = ["Applied", "Assessment", "Interview", "Recruiter contacted", "Follow-up sent", "Offer received", "Rejected", "Note"]


def parse_date(value, field_name, optional=False):
    if not value and optional:
        return None
    if not value:
        raise ValueError(f"{field_name} is required.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"Please enter a valid {field_name.lower()}.")


def selected_value(field, choices, other_field):
    value = request.form.get(field, "").strip()
    if value == "Other":
        other = request.form.get(other_field, "").strip()
        if not other:
            raise ValueError(f"Please specify the other {field.replace('_', ' ')}.")
        return other[:150]
    if value and value not in choices:
        # Allow an already saved custom value on edit, but only if explicitly provided via Other.
        raise ValueError(f"Please choose a valid {field.replace('_', ' ')}.")
    return value


def owned_application(application_id):
    return Application.query.filter_by(id=application_id, user_id=current_user.id).first_or_404()


def record_event(item, event_type, details="", event_date=None):
    db.session.add(ApplicationEvent(application_id=item.id, event_type=event_type,
                                    details=details, event_date=event_date or date.today()))


def application_form_values(item=None):
    def val(field, default=""):
        if item is not None:
            return getattr(item, field) or default
        return request.form.get(field, default)
    return val


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def index():
    return redirect(url_for("dashboard") if current_user.is_authenticated else url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("Please complete every required field.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Account created. Welcome to your tracker!", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    base_query = Application.query.filter_by(user_id=current_user.id, archived=False)
    query = base_query
    search = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    priority_filter = request.args.get("priority", "").strip()
    sort = request.args.get("sort", "date")
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Application.company.ilike(pattern), Application.job_role.ilike(pattern),
                                 Application.location.ilike(pattern), Application.notes.ilike(pattern)))
    if status_filter in STATUSES:
        query = query.filter_by(status=status_filter)
    if priority_filter in PRIORITIES:
        query = query.filter_by(priority=priority_filter)
    if sort == "company":
        query = query.order_by(Application.company.asc())
    elif sort == "priority":
        query = query.order_by(case((Application.priority == "High", 1), (Application.priority == "Medium", 2), else_=3), Application.application_date.desc())
    else:
        query = query.order_by(Application.application_date.desc(), Application.id.desc())
    applications = query.all()
    all_apps = base_query.all()
    counts = {status: sum(1 for item in all_apps if item.status == status) for status in STATUSES}
    counts["Other"] = sum(1 for item in all_apps if item.status not in STATUSES or item.status == "Other")
    upcoming = base_query.filter(Application.interview_date >= date.today(), Application.status == "Interview").order_by(Application.interview_date.asc()).limit(5).all()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    applied_this_week = base_query.filter(Application.application_date >= week_start).count()
    tasks = Task.query.filter_by(user_id=current_user.id, completed=False).order_by(Task.due_date.asc()).limit(5).all()
    due_followups = base_query.filter(Application.follow_up_date <= today, Application.follow_up_date.isnot(None)).all()
    overdue_tasks = Task.query.filter_by(user_id=current_user.id, completed=False).filter(Task.due_date < today).count()
    selected_count = counts.get("Selected", 0) + counts.get("Offer", 0)
    interviews_count = counts.get("Interview", 0)
    conversion = round((selected_count / len(all_apps)) * 100, 1) if all_apps else 0
    interview_rate = round((interviews_count / len(all_apps)) * 100, 1) if all_apps else 0
    month_labels, month_values = [], []
    for offset in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=offset * 28)).replace(day=1)
        next_month = (month_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_labels.append(month_date.strftime("%b %Y"))
        month_values.append(base_query.filter(Application.application_date >= month_date, Application.application_date < next_month).count())
    top_companies = db.session.query(Application.company, func.count(Application.id).label("n")).filter_by(user_id=current_user.id, archived=False).group_by(Application.company).order_by(func.count(Application.id).desc()).limit(5).all()
    return render_template("dashboard.html", applications=applications, counts=counts, total=len(all_apps), statuses=STATUSES,
        search=search, status_filter=status_filter, priority_filter=priority_filter, sort=sort, upcoming=upcoming, today=today,
        applied_this_week=applied_this_week, weekly_goal=max(current_user.weekly_goal or 5, 1), tasks=tasks,
        due_followups=due_followups, overdue_tasks=overdue_tasks, conversion=conversion, interview_rate=interview_rate,
        month_labels=month_labels, month_values=month_values, top_companies=top_companies, archived_count=Application.query.filter_by(user_id=current_user.id, archived=True).count())


def save_application(item=None):
    company = request.form.get("company", "").strip()
    role = request.form.get("job_role", "").strip()
    if not company or not role:
        raise ValueError("Company and job role are required.")
    status = selected_value("status", STATUSES, "status_other")
    interview_type = selected_value("interview_type", INTERVIEW_TYPES, "interview_type_other")
    employment_type = selected_value("employment_type", EMPLOYMENT_TYPES, "employment_type_other")
    priority = selected_value("priority", PRIORITIES, "priority_other") or "Medium"
    source = selected_value("source", SOURCES, "source_other")
    values = {
        "company": company, "job_role": role,
        "location": request.form.get("location", "").strip(),
        "application_date": parse_date(request.form.get("application_date"), "application date"),
        "status": status,
        "interview_date": parse_date(request.form.get("interview_date"), "interview date", optional=True),
        "interview_type": interview_type, "source": source,
        "notes": request.form.get("notes", "").strip(),
        "job_description": request.form.get("job_description", "").strip(),
        "job_url": request.form.get("job_url", "").strip(),
        "salary": request.form.get("salary", "").strip(),
        "employment_type": employment_type, "priority": priority,
        "recruiter_name": request.form.get("recruiter_name", "").strip(),
        "recruiter_email": request.form.get("recruiter_email", "").strip(),
        "recruiter_phone": request.form.get("recruiter_phone", "").strip(),
        "recruiter_url": request.form.get("recruiter_url", "").strip(),
        "follow_up_date": parse_date(request.form.get("follow_up_date"), "follow-up date", optional=True),
        "assessment_deadline": parse_date(request.form.get("assessment_deadline"), "assessment deadline", optional=True),
        "resume_version": request.form.get("resume_version", "").strip(),
    }
    for url_field in ("job_url", "recruiter_url"):
        if values[url_field] and not values[url_field].startswith(("https://", "http://")):
            raise ValueError(f"{url_field.replace('_', ' ').title()} must start with http:// or https://.")
    if item is None:
        item = Application(user_id=current_user.id, **values)
        db.session.add(item)
        db.session.flush()
        record_event(item, "Application created", f"Added application to {company}.", values["application_date"])
    else:
        old_status = item.status
        for key, value in values.items():
            setattr(item, key, value)
        if old_status != item.status:
            record_event(item, "Status changed", f"{old_status} → {item.status}")
    return item


@app.route("/applications/add", methods=["GET", "POST"])
@login_required
def add_application():
    if request.method == "POST":
        try:
            item = save_application()
            db.session.commit()
            flash("Application added successfully.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("application_form.html", item=None, statuses=STATUSES, interview_types=INTERVIEW_TYPES,
        employment_types=EMPLOYMENT_TYPES, priorities=PRIORITIES, sources=SOURCES, today=date.today().isoformat())


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
@login_required
def edit_application(application_id):
    item = owned_application(application_id)
    if request.method == "POST":
        try:
            old_status = item.status
            save_application(item)
            db.session.commit()
            flash("Application updated.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template("application_form.html", item=item, statuses=STATUSES, interview_types=INTERVIEW_TYPES,
        employment_types=EMPLOYMENT_TYPES, priorities=PRIORITIES, sources=SOURCES, today=date.today().isoformat())


@app.route("/applications/<int:application_id>/delete", methods=["POST"])
@login_required
def delete_application(application_id):
    item = owned_application(application_id)
    db.session.delete(item)
    db.session.commit()
    flash("Application deleted.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/applications/<int:application_id>/archive", methods=["POST"])
@login_required
def archive_application(application_id):
    item = owned_application(application_id)
    item.archived = not item.archived
    db.session.commit()
    flash("Application archived." if item.archived else "Application restored.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/applications/<int:application_id>/event", methods=["POST"])
@login_required
def add_event(application_id):
    item = owned_application(application_id)
    event_type = request.form.get("event_type", "Note").strip()
    details = request.form.get("details", "").strip()
    if event_type not in EVENT_TYPES or not details:
        flash("Choose an event type and enter a note.", "error")
    else:
        try:
            event_date = parse_date(request.form.get("event_date"), "event date")
            db.session.add(ApplicationEvent(application_id=item.id, event_type=event_type, details=details, event_date=event_date))
            db.session.commit()
            flash("Timeline event added.", "success")
        except ValueError as error:
            flash(str(error), "error")
    return redirect(url_for("application_detail", application_id=item.id))


@app.route("/applications/<int:application_id>")
@login_required
def application_detail(application_id):
    item = owned_application(application_id)
    return render_template("application_detail.html", item=item, event_types=EVENT_TYPES, today=date.today().isoformat())


@app.route("/interviews/add/<int:application_id>", methods=["POST"])
@login_required
def add_interview(application_id):
    item = owned_application(application_id)
    try:
        interview_date = parse_date(request.form.get("interview_date"), "interview date")
        round_name = request.form.get("round_name", "Interview").strip() or "Interview"
        kind = request.form.get("interview_type", "").strip()
        if kind == "Other":
            kind = request.form.get("interview_type_other", "").strip()
            if not kind:
                raise ValueError("Please specify the other interview type.")
        db.session.add(Interview(application_id=item.id, round_name=round_name, interview_type=kind,
                                 interview_date=interview_date, notes=request.form.get("notes", "").strip()))
        item.interview_date = interview_date
        item.status = "Interview"
        record_event(item, "Interview scheduled", f"{round_name} · {kind or 'Interview'}", interview_date)
        db.session.commit()
        flash("Interview round added.", "success")
    except ValueError as error:
        flash(str(error), "error")
    return redirect(url_for("application_detail", application_id=item.id))


@app.route("/tasks", methods=["GET", "POST"])
@login_required
def tasks_page():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Task title is required.", "error")
        else:
            try:
                due = parse_date(request.form.get("due_date"), "due date", optional=True)
                app_id = request.form.get("application_id", type=int)
                if app_id and not Application.query.filter_by(id=app_id, user_id=current_user.id).first():
                    raise ValueError("Choose one of your own applications.")
                db.session.add(Task(user_id=current_user.id, title=title, description=request.form.get("description", "").strip(),
                                    due_date=due, priority=request.form.get("priority", "Medium"), application_id=app_id))
                db.session.commit()
                flash("Task created.", "success")
                return redirect(url_for("tasks_page"))
            except ValueError as error:
                flash(str(error), "error")
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.completed.asc(), Task.due_date.asc()).all()
    apps = Application.query.filter_by(user_id=current_user.id, archived=False).order_by(Application.company.asc()).all()
    return render_template("tasks.html", tasks=tasks, applications=apps, today=date.today())


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.completed = not task.completed
    db.session.commit()
    return redirect(request.referrer or url_for("tasks_page"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "success")
    return redirect(url_for("tasks_page"))


@app.route("/calendar")
@login_required
def calendar_page():
    apps = Application.query.filter_by(user_id=current_user.id, archived=False).all()
    tasks = Task.query.filter_by(user_id=current_user.id).filter(Task.due_date.isnot(None)).all()
    events = []
    for item in apps:
        for field, label in ((item.application_date, "Applied"), (item.interview_date, "Interview"),
                             (item.follow_up_date, "Follow-up"), (item.assessment_deadline, "Assessment deadline")):
            if field:
                events.append({"date": field.isoformat(), "title": f"{label}: {item.company} — {item.job_role}", "url": url_for("application_detail", application_id=item.id)})
    for task in tasks:
        events.append({"date": task.due_date.isoformat(), "title": f"Task: {task.title}", "url": url_for("tasks_page")})
    return render_template("calendar.html", events=sorted(events, key=lambda e: e["date"]), today=date.today().isoformat())


@app.route("/board")
@login_required
def kanban_board():
    apps = Application.query.filter_by(user_id=current_user.id, archived=False).order_by(Application.application_date.desc()).all()
    board_statuses = ["Applied", "Assessment", "Interview", "Offer", "Selected", "Rejected", "Withdrawn", "Other"]
    return render_template("board.html", applications=apps, statuses=board_statuses)


@app.route("/applications/<int:application_id>/status", methods=["POST"])
@login_required
def update_status(application_id):
    item = owned_application(application_id)
    status = request.form.get("status", "")
    if status not in STATUSES:
        flash("Invalid status.", "error")
    else:
        old = item.status
        item.status = status
        if old != status:
            record_event(item, "Status changed", f"{old} → {status}")
        db.session.commit()
        flash("Application status updated.", "success")
    return redirect(request.referrer or url_for("kanban_board"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if not name or not email:
            flash("Name and email are required.", "error")
        elif existing:
            flash("That email is already in use.", "error")
        else:
            current_user.name = name
            current_user.email = email
            current_user.phone = request.form.get("phone", "").strip()
            current_user.education = request.form.get("education", "").strip()
            current_user.skills = request.form.get("skills", "").strip()
            current_user.target_role = request.form.get("target_role", "").strip()
            try:
                current_user.weekly_goal = max(1, min(200, int(request.form.get("weekly_goal", "5"))))
            except ValueError:
                current_user.weekly_goal = 5
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))
    return render_template("profile.html")


@app.route("/settings/theme", methods=["POST"])
@login_required
def toggle_theme():
    current_user.theme = "dark" if current_user.theme != "dark" else "light"
    db.session.commit()
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/export.csv")
@login_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    fields = ["Company", "Job role", "Location", "Application date", "Status", "Interview date", "Interview type", "Source", "Salary", "Employment type", "Priority", "Job URL", "Follow-up date", "Assessment deadline", "Recruiter name", "Recruiter email", "Recruiter phone", "Resume version", "Notes"]
    writer.writerow(fields)
    for a in Application.query.filter_by(user_id=current_user.id).order_by(Application.application_date.desc()).all():
        writer.writerow([a.company, a.job_role, a.location, a.application_date, a.status, a.interview_date or "", a.interview_type, a.source, a.salary, a.employment_type, a.priority, a.job_url, a.follow_up_date or "", a.assessment_deadline or "", a.recruiter_name, a.recruiter_email, a.recruiter_phone, a.resume_version, a.notes])
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=careertrack-applications.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response



@app.route("/import.csv", methods=["GET", "POST"])
@login_required
def import_csv():
    if request.method == "POST":
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename.lower().endswith(".csv"):
            flash("Choose a CSV file to import.", "error")
            return redirect(url_for("import_csv"))
        try:
            stream = io.StringIO(uploaded.stream.read().decode("utf-8-sig"), newline=None)
            reader = csv.DictReader(stream)
            if not reader.fieldnames or not {"company", "job_role"}.issubset({h.strip().lower() for h in reader.fieldnames}):
                raise ValueError("CSV must include at least Company and Job role columns (company, job_role).")
            # Normalize header names so exported CareerTrack CSV files can be re-imported.
            count = 0
            for row in reader:
                normalized = {str(k or "").strip().lower().replace(" ", "_"): (v or "").strip() for k, v in row.items()}
                company = normalized.get("company", "")
                role = normalized.get("job_role", normalized.get("job_role_", ""))
                if not company or not role:
                    continue
                raw_date = normalized.get("application_date", "") or normalized.get("date_applied", "")
                try:
                    applied = date.fromisoformat(raw_date) if raw_date else date.today()
                except ValueError:
                    applied = date.today()
                status = normalized.get("status", "Applied") or "Applied"
                if status not in STATUSES:
                    status = status[:60]
                item = Application(user_id=current_user.id, company=company[:150], job_role=role[:150],
                    location=normalized.get("location", "")[:150], application_date=applied, status=status,
                    interview_type=normalized.get("interview_type", "")[:100], source=normalized.get("source", "")[:100],
                    salary=normalized.get("salary", "")[:100], employment_type=normalized.get("employment_type", "")[:100],
                    priority=normalized.get("priority", "Medium")[:20], notes=normalized.get("notes", ""))
                db.session.add(item)
                count += 1
            db.session.commit()
            flash(f"Imported {count} application(s). Rows without a company or job role were skipped.", "success")
            return redirect(url_for("dashboard"))
        except (UnicodeDecodeError, csv.Error, ValueError) as error:
            db.session.rollback()
            flash(f"Could not import CSV: {error}", "error")
            return redirect(url_for("import_csv"))
    return render_template("import_csv.html")


@app.route("/account/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")
    if not current_user.check_password(current_password):
        flash("Your current password is incorrect.", "error")
    elif len(new_password) < 8:
        flash("New password must contain at least 8 characters.", "error")
    elif new_password != confirm_password:
        flash("New password and confirmation do not match.", "error")
    else:
        current_user.set_password(new_password)
        db.session.commit()
        flash("Password changed successfully.", "success")
    return redirect(url_for("profile"))


@app.route("/archive")
@login_required
def archive_page():
    applications = Application.query.filter_by(user_id=current_user.id, archived=True).order_by(Application.application_date.desc()).all()
    return render_template("archive.html", applications=applications)


@app.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    user = db.session.get(User, current_user.id)
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash("Your account and associated data were deleted.", "success")
    return redirect(url_for("register"))


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


@app.errorhandler(413)
def too_large(_error):
    flash("That upload is too large. Maximum request size is 8 MB.", "error")
    return redirect(request.referrer or url_for("dashboard"))


def migrate_sqlite_columns():
    """Add newly introduced columns to older SQLite databases without deleting user data."""
    if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        return
    inspector = db.inspect(db.engine)
    existing_tables = inspector.get_table_names()
    if "application" in existing_tables:
        existing = {c["name"] for c in inspector.get_columns("application")}
        additions = {
            "job_description": "TEXT DEFAULT ''", "job_url": "VARCHAR(500) DEFAULT ''", "salary": "VARCHAR(100) DEFAULT ''",
            "employment_type": "VARCHAR(100) DEFAULT ''", "priority": "VARCHAR(20) DEFAULT 'Medium'", "recruiter_name": "VARCHAR(120) DEFAULT ''",
            "recruiter_email": "VARCHAR(150) DEFAULT ''", "recruiter_phone": "VARCHAR(50) DEFAULT ''", "recruiter_url": "VARCHAR(500) DEFAULT ''",
            "follow_up_date": "DATE", "assessment_deadline": "DATE", "archived": "BOOLEAN NOT NULL DEFAULT 0", "resume_version": "VARCHAR(120) DEFAULT ''"
        }
        with db.engine.begin() as conn:
            for name, definition in additions.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE application ADD COLUMN {name} {definition}"))
    if "user" in existing_tables:
        existing = {c["name"] for c in inspector.get_columns("user")}
        additions = {"phone": "VARCHAR(40) DEFAULT ''", "education": "VARCHAR(180) DEFAULT ''", "skills": "TEXT DEFAULT ''", "target_role": "VARCHAR(150) DEFAULT ''", "weekly_goal": "INTEGER DEFAULT 5", "theme": "VARCHAR(20) DEFAULT 'light'", "role": "VARCHAR(30) NOT NULL DEFAULT 'user'"}
        with db.engine.begin() as conn:
            for name, definition in additions.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE user ADD COLUMN {name} {definition}"))


with app.app_context():
    db.create_all()
    migrate_sqlite_columns()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
