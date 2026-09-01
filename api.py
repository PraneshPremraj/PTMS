

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from models import Project, Task, ProjectMember

api_bp = Blueprint("api", __name__, url_prefix="/api")


def serialize_task(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "assigned_to": task.assigned_to,
        "assignee_name": task.assignee.name if task.assignee else None,
        "project_id": task.project_id,
        "project_name": task.project.name,
    }


def serialize_project(project, completion=None):
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "manager_id": project.manager_id,
        "deadline": project.deadline.isoformat() if project.deadline else None,
        "completion_percent": completion,
    }


def get_completion_percentage(project_id):
    total = Task.query.filter_by(project_id=project_id).count()
    if total == 0:
        return 0
    done = Task.query.filter_by(project_id=project_id, status="done").count()
    return round((done / total) * 100, 1)


@api_bp.route("/projects", methods=["GET"])
@login_required
def api_list_projects():
    if current_user.role == "project_manager":
        projects = Project.query.filter_by(manager_id=current_user.id).all()
    else:
        project_ids = [pm.project_id for pm in ProjectMember.query.filter_by(user_id=current_user.id).all()]
        projects = Project.query.filter(Project.id.in_(project_ids)).all() if project_ids else []

    data = [serialize_project(p, get_completion_percentage(p.id)) for p in projects]
    return jsonify({"count": len(data), "projects": data})


@api_bp.route("/projects/<int:project_id>/tasks", methods=["GET"])
@login_required
def api_project_tasks(project_id):
    project = Project.query.get_or_404(project_id)

    is_manager = project.manager_id == current_user.id
    is_member = ProjectMember.query.filter_by(
        project_id=project_id, user_id=current_user.id
    ).first() is not None
    if not (is_manager or is_member):
        return jsonify({"error": "Forbidden"}), 403

    tasks = Task.query.filter_by(project_id=project_id).all()
    return jsonify({"count": len(tasks), "tasks": [serialize_task(t) for t in tasks]})


@api_bp.route("/my-tasks", methods=["GET"])
@login_required
def api_my_tasks():
    tasks = Task.query.filter_by(assigned_to=current_user.id).all()
    return jsonify({"count": len(tasks), "tasks": [serialize_task(t) for t in tasks]})


@api_bp.route("/tasks", methods=["GET"])
@login_required
def api_search_tasks():
    """
    Search/filter across every task the current user is allowed to see.

    Query params (all optional, combine freely):
        status      - to_do | in_progress | done
        priority    - low | medium | high
        project_id  - integer
        search      - case-insensitive match against the task title

    Examples:
        /api/tasks?status=in_progress
        /api/tasks?priority=high&search=login
        /api/tasks?project_id=3&status=to_do
    """
    if current_user.role == "project_manager":
        project_ids = [p.id for p in Project.query.filter_by(manager_id=current_user.id).all()]
        if not project_ids:
            return jsonify({"count": 0, "tasks": []})
        query = Task.query.filter(Task.project_id.in_(project_ids))
    else:
        query = Task.query.filter_by(assigned_to=current_user.id)

    status = request.args.get("status")
    priority = request.args.get("priority")
    project_id = request.args.get("project_id", type=int)
    search = request.args.get("search")

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    tasks = query.order_by(Task.due_date.asc()).all()
    return jsonify({"count": len(tasks), "tasks": [serialize_task(t) for t in tasks]})