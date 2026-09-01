from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from extensions import db
from models import Project, Task, ProjectMember, User

projects_bp = Blueprint("projects", __name__)


PROJECT_DESCRIPTIONS = {
    "Website Redesign": "Modernizing the public-facing website with a new design system, faster load times, and mobile-first layouts.",
    "Mobile App Launch": "Building and shipping the company's first native mobile app for iOS and Android, including onboarding and push notifications.",
    "CRM Migration": "Migrating customer data and workflows from the legacy CRM to a new unified platform with zero downtime.",
    "Marketing Campaign": "Planning and executing a multi-channel campaign to build awareness ahead of the next product launch.",
    "Internal Tools Upgrade": "Rebuilding internal admin tools with better performance, clearer permissions, and a cleaner interface.",
    "Customer Portal": "Launching a self-service portal where customers can manage their accounts, invoices, and support tickets.",
    "Data Pipeline": "Designing a scalable ETL pipeline to consolidate data from multiple sources into a single warehouse.",
    "Security Audit": "Running a full security review of infrastructure, access controls, and third-party integrations.",
    "Onboarding Revamp": "Redesigning the new-hire onboarding experience to shorten ramp-up time and improve retention.",
    "API Integration": "Integrating third-party payment and shipping providers into the core platform via REST APIs.",
    "Analytics Dashboard": "Building an internal analytics dashboard to track key business metrics in real time.",
    "Support Portal": "Creating a knowledge base and ticketing system to streamline customer support operations.",
}


def get_completion_percentage(project_id):
    total = Task.query.filter_by(project_id=project_id).count()
    if total == 0:
        return 0
    done = Task.query.filter_by(project_id=project_id, status="done").count()
    return round((done / total) * 100, 1)


@projects_bp.route("/projects")
@login_required
def list_projects():
    if current_user.role == "project_manager":
        # PMs see only projects they personally manage
        projects = Project.query.filter_by(manager_id=current_user.id).all()
    else:
        # Team members see only projects they've been added to
        member_links = ProjectMember.query.filter_by(user_id=current_user.id).all()
        project_ids = [link.project_id for link in member_links]
        projects = Project.query.filter(Project.id.in_(project_ids)).all() if project_ids else []

    project_rows = []
    for p in projects:
        total_tasks = Task.query.filter_by(project_id=p.id).count()
        project_rows.append({
            "project": p,
            "description": PROJECT_DESCRIPTIONS.get(p.name, p.description),
            "total_tasks": total_tasks,
            "completion": get_completion_percentage(p.id)
        })

    # NEW: PM's team members, so the "Create Project" form can offer them for assignment
    team_members = []
    if current_user.role == "project_manager":
        team_members = User.query.filter_by(reports_to=current_user.id, role="team_member").all()

    return render_template("projects/list.html", project_rows=project_rows, team_members=team_members)


@projects_bp.route("/projects/<int:project_id>")
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)

    is_manager = project.manager_id == current_user.id
    is_member = ProjectMember.query.filter_by(
        project_id=project_id, user_id=current_user.id
    ).first() is not None

    if not (is_manager or is_member):
        abort(403)

    members = [pm.user for pm in ProjectMember.query.filter_by(project_id=project_id).all()]
    tasks = Task.query.filter_by(project_id=project_id).all()

    task_rows = [
        {"task": t, "assignee_name": t.assignee.name if t.assignee else "Unassigned"}
        for t in tasks
    ]

    return render_template(
        "projects/detail.html",
        project=project,
        description=PROJECT_DESCRIPTIONS.get(project.name, project.description),
        members=members,
        task_rows=task_rows,
        completion=get_completion_percentage(project_id),
        is_manager=is_manager,
    )


# ---- NEW: Create Project (additive, doesn't touch anything above) ----

@projects_bp.route("/projects/new", methods=["POST"])
@login_required
def create_project():
    if current_user.role != "project_manager":
        flash("Only Project Managers can create projects.")
        return redirect(url_for("projects.list_projects"))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    deadline_raw = request.form.get("deadline", "").strip()
    member_ids = request.form.getlist("members")

    if not name:
        flash("Project name is required.")
        return redirect(url_for("projects.list_projects"))

    deadline = None
    if deadline_raw:
        try:
            deadline = datetime.strptime(deadline_raw, "%Y-%m-%d").date()
        except ValueError:
            deadline = None

    project = Project(
        name=name,
        description=description or None,
        manager_id=current_user.id,
        deadline=deadline
    )
    db.session.add(project)
    db.session.commit()

    # Only allow assigning members who genuinely report to this PM
    if member_ids:
        valid_members = User.query.filter(
            User.id.in_(member_ids),
            User.reports_to == current_user.id,
            User.role == "team_member"
        ).all()
        for member in valid_members:
            db.session.add(ProjectMember(project_id=project.id, user_id=member.id))
        db.session.commit()

    flash(f'Project "{name}" created.')
    return redirect(url_for("projects.project_detail", project_id=project.id))