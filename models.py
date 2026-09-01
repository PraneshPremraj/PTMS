from datetime import datetime
from extensions import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    
    role = db.Column(db.String(30), nullable=False)

    
    designation = db.Column(db.String(50), nullable=True)

    
    reports_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ---- NEW: personal description shown on the user's profile page ----
    bio = db.Column(db.Text, nullable=True)

    
    subordinates = db.relationship(
        "User",
        backref=db.backref("manager", remote_side=[id])
    )

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"


class Project(db.Model):
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    
    manager_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    manager = db.relationship("User", backref="managed_projects")

    def __repr__(self):
        return f"<Project {self.name}>"


class ProjectMember(db.Model):
    __tablename__ = "project_member"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    project = db.relationship("Project", backref="members")
    user = db.relationship("User", backref="project_memberships")

    def __repr__(self):
        return f"<ProjectMember project={self.project_id} user={self.user_id}>"


class Task(db.Model):
    __tablename__ = "task"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # to_do, in_progress, done
    status = db.Column(db.String(20), nullable=False, default="to_do")

    # low, medium, high
    priority = db.Column(db.String(10), nullable=False, default="medium")

    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", backref="tasks")
    assignee = db.relationship("User", backref="assigned_tasks")

    def __repr__(self):
        return f"<Task {self.title} ({self.status})>"


class Comment(db.Model):
    __tablename__ = "comment"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship("Task", backref="comments")
    user = db.relationship("User", backref="comments")

    def __repr__(self):
        return f"<Comment task={self.task_id} user={self.user_id}>"


class Attachment(db.Model):
    __tablename__ = "attachment"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship("Task", backref="attachments")
    uploader = db.relationship("User", backref="uploaded_attachments")

    def __repr__(self):
        return f"<Attachment {self.original_filename}>"