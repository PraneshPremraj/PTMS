from datetime import date, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models import Project, Task

dashboard = Blueprint("dashboard", __name__)

# NEW: how many days ahead counts as "coming up soon" for a reminder
REMINDER_WINDOW_DAYS = 3


@dashboard.route("/dashboard")
@login_required
def index():
    if current_user.role == "project_manager":
        projects = Project.query.filter_by(manager_id=current_user.id).all()
        project_ids = [p.id for p in projects]
        tasks = Task.query.filter(Task.project_id.in_(project_ids)).all() if project_ids else []
        primary_label = "Total Projects"
        primary_count = len(projects)
    else:
        tasks = Task.query.filter_by(assigned_to=current_user.id).all()
        primary_label = "Assigned Tasks"
        primary_count = len(tasks)

    to_do = len([t for t in tasks if t.status == "to_do"])
    in_progress = len([t for t in tasks if t.status == "in_progress"])
    done = len([t for t in tasks if t.status == "done"])
    overdue = len([
        t for t in tasks
        if t.due_date and t.due_date < date.today() and t.status != "done"
    ])

    stats = {
        "primary_label": primary_label,
        "primary_count": primary_count,
        "in_progress": in_progress,
        "done": done,
        "overdue": overdue,
    }

    chart_data = {
        "labels": ["To Do", "In Progress", "Done"],
        "values": [to_do, in_progress, done],
    }

    # ---- NEW: due-date reminders (additive only, reuses the `tasks` list above) ----
    today = date.today()
    reminder_cutoff = today + timedelta(days=REMINDER_WINDOW_DAYS)

    reminders = []
    for t in tasks:
        if t.due_date and t.status != "done" and t.due_date <= reminder_cutoff:
            days_left = (t.due_date - today).days
            reminders.append({
                "task": t,
                "days_left": days_left,
                "is_overdue": days_left < 0,
            })
    reminders.sort(key=lambda r: r["task"].due_date)

    return render_template(
        "dashboard.html",
        stats=stats,
        chart_data=chart_data,
        reminders=reminders,
    )