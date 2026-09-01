from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from extensions import db
from models import User, Task, ProjectMember

team_bp = Blueprint("team", __name__)

# Allowed designations, shown in the "Add member" dropdown.
DESIGNATIONS = ["Team Lead", "Senior Software Engineer", "Software Engineer", "Software Engineer Intern"]


def make_email(name):
    return name.strip().lower().replace(" ", ".") + "@company.com"


@team_bp.route("/team")
@login_required
def list_team():
    if current_user.role != "project_manager":
        flash("Only Project Managers can view the team page.")
        return redirect(url_for("dashboard.index"))

    members = User.query.filter_by(reports_to=current_user.id, role="team_member").all()

    member_rows = []
    for m in members:
        member_rows.append({
            "member": m,
            "task_count": Task.query.filter_by(assigned_to=m.id).count()
        })

    return render_template("team/list.html", member_rows=member_rows, designations=DESIGNATIONS)


@team_bp.route("/team/add", methods=["POST"])
@login_required
def add_member():
    if current_user.role != "project_manager":
        flash("Only Project Managers can add team members.")
        return redirect(url_for("dashboard.index"))

    name = request.form.get("name", "").strip()
    designation = request.form.get("designation", "").strip() or "Software Engineer"

    if not name:
        flash("Name is required.")
        return redirect(url_for("team.list_team"))

    if designation not in DESIGNATIONS:
        designation = "Software Engineer"

    email = make_email(name)
    if User.query.filter_by(email=email).first():
        flash(f"A user with email {email} already exists. Try a different name.")
        return redirect(url_for("team.list_team"))

    new_member = User(
        name=name,
        email=email,
        password_hash=generate_password_hash("password123"),
        role="team_member",
        designation=designation,
        reports_to=current_user.id
    )
    db.session.add(new_member)
    db.session.commit()

    flash(f"{name} ({designation}) added to your team. Login: {email} / password123")
    return redirect(url_for("team.list_team"))


@team_bp.route("/team/<int:member_id>/remove", methods=["POST"])
@login_required
def remove_member(member_id):
    if current_user.role != "project_manager":
        flash("Only Project Managers can remove team members.")
        return redirect(url_for("dashboard.index"))

    member = User.query.get_or_404(member_id)

    if member.reports_to != current_user.id:
        flash("You can only remove members of your own team.")
        return redirect(url_for("team.list_team"))

    # Unassign their tasks and remove them from any projects before deleting
    Task.query.filter_by(assigned_to=member.id).update({"assigned_to": None})
    ProjectMember.query.filter_by(user_id=member.id).delete()
    db.session.delete(member)
    db.session.commit()

    flash(f"{member.name} removed from your team.")
    return redirect(url_for("team.list_team"))


# ---- NEW: change a member's designation any time (additive) ----

@team_bp.route("/team/<int:member_id>/designation", methods=["POST"])
@login_required
def update_designation(member_id):
    if current_user.role != "project_manager":
        flash("Only Project Managers can update designations.")
        return redirect(url_for("dashboard.index"))

    member = User.query.get_or_404(member_id)

    if member.reports_to != current_user.id:
        flash("You can only update designations for your own team.")
        return redirect(url_for("team.list_team"))

    new_designation = request.form.get("designation", "").strip()
    if new_designation not in DESIGNATIONS:
        flash("Invalid designation.")
        return redirect(url_for("team.list_team"))

    member.designation = new_designation
    db.session.commit()
    flash(f"{member.name}'s designation updated to {new_designation}.")
    return redirect(url_for("team.list_team"))


# ---- Task Assigned feature (unchanged from before) ----

@team_bp.route("/team/tasks")
@login_required
def assigned_overview():
    """Lists the PM's team members so they can click into any one person's tasks."""
    if current_user.role != "project_manager":
        flash("Only Project Managers can view this page.")
        return redirect(url_for("dashboard.index"))

    members = User.query.filter_by(reports_to=current_user.id, role="team_member").all()

    member_rows = []
    for m in members:
        member_rows.append({
            "member": m,
            "task_count": Task.query.filter_by(assigned_to=m.id).count()
        })

    return render_template("team/assigned_overview.html", member_rows=member_rows)


@team_bp.route("/team/<int:member_id>/tasks")
@login_required
def member_tasks(member_id):
    """Shows every task assigned to one specific team member."""
    if current_user.role != "project_manager":
        flash("Only Project Managers can view this page.")
        return redirect(url_for("dashboard.index"))

    member = User.query.get_or_404(member_id)

    if member.reports_to != current_user.id:
        flash("You can only view tasks for your own team members.")
        return redirect(url_for("team.assigned_overview"))

    tasks = Task.query.filter_by(assigned_to=member.id).order_by(Task.due_date.asc()).all()
    task_rows = [{"task": t, "project_name": t.project.name} for t in tasks]

    return render_template("team/member_tasks.html", member=member, task_rows=task_rows)