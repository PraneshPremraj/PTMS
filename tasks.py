import os
import uuid
from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, abort, current_app, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import Project, ProjectMember, Task, Comment, Attachment

tasks_bp = Blueprint("tasks", __name__)


def _ensure_project_access(project):
    """Allow the PM who manages this project, or any member added to it. Abort otherwise."""
    is_manager = project.manager_id == current_user.id
    is_member = ProjectMember.query.filter_by(
        project_id=project.id, user_id=current_user.id
    ).first() is not None

    if not (is_manager or is_member):
        abort(403)


def _allowed_file(filename):
    """NEW: only allow file extensions listed in Config.ALLOWED_EXTENSIONS."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", set())


@tasks_bp.route("/my-tasks")
@login_required
def my_tasks():
    tasks = (
        Task.query.filter_by(assigned_to=current_user.id)
        .order_by(Task.due_date.asc())
        .all()
    )
    task_rows = [{"task": t, "project_name": t.project.name} for t in tasks]
    return render_template("tasks/my_tasks.html", task_rows=task_rows)


@tasks_bp.route("/projects/<int:project_id>/tasks/new", methods=["POST"])
@login_required
def create_task(project_id):
    project = Project.query.get_or_404(project_id)

    if project.manager_id != current_user.id:
        flash("Only the project manager can create tasks for this project.")
        return redirect(url_for("projects.project_detail", project_id=project_id))

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    assigned_to = request.form.get("assigned_to") or None
    priority = request.form.get("priority", "medium")
    due_date_raw = request.form.get("due_date", "").strip()

    if not title:
        flash("Task title is required.")
        return redirect(url_for("projects.project_detail", project_id=project_id))

    # Only allow assigning to someone who is actually a member of this project
    if assigned_to:
        is_member = ProjectMember.query.filter_by(
            project_id=project_id, user_id=assigned_to
        ).first()
        if not is_member:
            flash("You can only assign tasks to members of this project.")
            return redirect(url_for("projects.project_detail", project_id=project_id))

    due_date = None
    if due_date_raw:
        try:
            due_date = datetime.strptime(due_date_raw, "%Y-%m-%d").date()
        except ValueError:
            due_date = None

    task = Task(
        project_id=project_id,
        title=title,
        description=description or None,
        assigned_to=int(assigned_to) if assigned_to else None,
        priority=priority if priority in ("low", "medium", "high") else "medium",
        due_date=due_date,
    )
    db.session.add(task)
    db.session.commit()

    flash(f'Task "{title}" created.')
    return redirect(url_for("projects.project_detail", project_id=project_id))


@tasks_bp.route("/tasks/<int:task_id>")
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    _ensure_project_access(project)

    comments = (
        Comment.query.filter_by(task_id=task.id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    # NEW: attachments for this task, newest first
    attachments = (
        Attachment.query.filter_by(task_id=task.id)
        .order_by(Attachment.uploaded_at.desc())
        .all()
    )
    is_manager = project.manager_id == current_user.id

    return render_template(
        "tasks/detail.html",
        task=task,
        project=project,
        comments=comments,
        attachments=attachments,
        is_manager=is_manager,
    )


@tasks_bp.route("/tasks/<int:task_id>/comment", methods=["POST"])
@login_required
def add_comment(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    _ensure_project_access(project)

    text = request.form.get("text", "").strip()
    if text:
        db.session.add(Comment(task_id=task.id, user_id=current_user.id, text=text))
        db.session.commit()
    else:
        flash("Comment can't be empty.")

    return redirect(url_for("tasks.task_detail", task_id=task_id))


@tasks_bp.route("/tasks/<int:task_id>/status", methods=["POST"])
@login_required
def update_status(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    _ensure_project_access(project)

    is_manager = project.manager_id == current_user.id
    is_assignee = task.assigned_to == current_user.id
    if not (is_manager or is_assignee):
        flash("You can only update the status of tasks assigned to you.")
        return redirect(url_for("tasks.task_detail", task_id=task_id))

    new_status = request.form.get("status")
    if new_status in ("to_do", "in_progress", "done"):
        task.status = new_status
        db.session.commit()
        flash("Task status updated.")
    else:
        flash("Invalid status.")

    return redirect(url_for("tasks.task_detail", task_id=task_id))


# ---- NEW: file attachments (additive, doesn't touch anything above) ----

@tasks_bp.route("/tasks/<int:task_id>/attachments", methods=["POST"])
@login_required
def upload_attachment(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    _ensure_project_access(project)

    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Choose a file to upload.")
        return redirect(url_for("tasks.task_detail", task_id=task_id))

    if not _allowed_file(file.filename):
        flash("That file type isn't allowed.")
        return redirect(url_for("tasks.task_detail", task_id=task_id))

    original_name = secure_filename(file.filename)
    # Prefix with a random id so two people uploading "report.pdf" never collide
    stored_name = f"{uuid.uuid4().hex}_{original_name}"

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, stored_name))

    db.session.add(Attachment(
        task_id=task.id,
        uploaded_by=current_user.id,
        original_filename=original_name,
        stored_filename=stored_name,
    ))
    db.session.commit()

    flash(f'"{original_name}" uploaded.')
    return redirect(url_for("tasks.task_detail", task_id=task_id))


@tasks_bp.route("/attachments/<int:attachment_id>/download")
@login_required
def download_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    _ensure_project_access(attachment.task.project)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(
        upload_folder,
        attachment.stored_filename,
        as_attachment=True,
        download_name=attachment.original_filename,
    )


@tasks_bp.route("/attachments/<int:attachment_id>/delete", methods=["POST"])
@login_required
def delete_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    task = attachment.task
    project = task.project
    _ensure_project_access(project)

    is_manager = project.manager_id == current_user.id
    is_uploader = attachment.uploaded_by == current_user.id
    if not (is_manager or is_uploader):
        flash("You can only remove attachments you uploaded.")
        return redirect(url_for("tasks.task_detail", task_id=task.id))

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, attachment.stored_filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(attachment)
    db.session.commit()
    flash("Attachment removed.")
    return redirect(url_for("tasks.task_detail", task_id=task.id))