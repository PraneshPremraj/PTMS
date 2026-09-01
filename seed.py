import random
from datetime import date, timedelta
from faker import Faker
from werkzeug.security import generate_password_hash
from sqlalchemy import text

from app_init import create_app
from extensions import db
from models import User, Project, ProjectMember, Task, Comment

fake = Faker()
app = create_app()

PASSWORD = generate_password_hash("password123")
TASK_STATUSES = ["to_do", "in_progress", "done"]
TASK_PRIORITIES = ["low", "medium", "high"]

_used_emails = set()


def make_email(name):
    base = name.strip().lower().replace(" ", ".")
    email = f"{base}@company.com"
    counter = 2
    while email in _used_emails:
        email = f"{base}{counter}@company.com"
        counter += 1
    _used_emails.add(email)
    return email


def make_user(name, role, reports_to=None):
    user = User(
        name=name,
        email=make_email(name),
        password_hash=PASSWORD,
        role=role,
        reports_to=reports_to
    )
    db.session.add(user)
    db.session.commit()
    return user


with app.app_context():
    db.session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    Comment.query.delete()
    Task.query.delete()
    ProjectMember.query.delete()
    Project.query.delete()
    User.query.delete()
    db.session.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    db.session.commit()

    # ---- Project Managers ----
    pm_names = ["Rahul Sharma", "Priya Nair", "Karthik Iyer", "Ananya Reddy", "Vikram Singh", "Divya Menon"]
    pms = [make_user(name, "project_manager") for name in pm_names]

    # ---- Team Members (~6 per PM) ----
    members = []
    for pm in pms:
        for _ in range(6):
            members.append(make_user(fake.name(), "team_member", reports_to=pm.id))

    print(f"Users created: {len(pms)} Project Managers, {len(members)} Team Members")
    for pm in pms:
        print(f"  PM login: {pm.email} / password123")

    # ---- Projects (2 per PM) ----
    project_types = ["Website Redesign", "Mobile App Launch", "CRM Migration", "Marketing Campaign",
                      "Internal Tools Upgrade", "Customer Portal", "Data Pipeline", "Security Audit",
                      "Onboarding Revamp", "API Integration", "Analytics Dashboard", "Support Portal"]
    random.shuffle(project_types)

    projects = []
    idx = 0
    for pm in pms:
        pm_members = [m for m in members if m.reports_to == pm.id]
        for _ in range(2):
            project = Project(
                name=project_types[idx % len(project_types)],
                description=fake.sentence(nb_words=12),
                manager_id=pm.id,
                deadline=date.today() + timedelta(days=random.randint(15, 90))
            )
            idx += 1
            db.session.add(project)
            db.session.commit()
            projects.append(project)

            chosen = random.sample(pm_members, min(len(pm_members), random.randint(3, 6)))
            for member in chosen:
                db.session.add(ProjectMember(project_id=project.id, user_id=member.id))
            db.session.commit()

    print(f"Projects created: {len(projects)}")

    # ---- Tasks + Comments ----
    task_verbs = ["Design", "Implement", "Test", "Review", "Fix", "Document", "Deploy", "Optimize", "Refactor", "Plan"]
    task_subjects = ["login page", "database schema", "API endpoint", "dashboard UI", "user roles",
                      "payment flow", "email notifications", "search feature", "error handling",
                      "mobile layout", "caching layer", "reporting module"]

    total_tasks, total_comments = 0, 0

    for project in projects:
        member_ids = [pm.user_id for pm in ProjectMember.query.filter_by(project_id=project.id).all()]
        if not member_ids:
            continue

        for _ in range(random.randint(5, 10)):
            task = Task(
                project_id=project.id,
                title=f"{random.choice(task_verbs)} {random.choice(task_subjects)}",
                description=fake.sentence(nb_words=10),
                assigned_to=random.choice(member_ids),
                status=random.choice(TASK_STATUSES),
                priority=random.choice(TASK_PRIORITIES),
                due_date=date.today() + timedelta(days=random.randint(-5, 45))
            )
            db.session.add(task)
            db.session.commit()
            total_tasks += 1

            if random.random() < 0.6:
                for _ in range(random.randint(1, 3)):
                    db.session.add(Comment(
                        task_id=task.id,
                        user_id=random.choice(member_ids),
                        text=fake.sentence(nb_words=8)
                    ))
                    total_comments += 1
        db.session.commit()

    print(f"Tasks created: {total_tasks}")
    print(f"Comments created: {total_comments}")
    print("\nSeed complete. All passwords: password123")