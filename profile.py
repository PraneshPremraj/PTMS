from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def view_profile():
    """Shows the logged-in user's own personal profile / description."""
    stats = {}

    if current_user.role == "project_manager":
        stats["projects"] = len(current_user.managed_projects)
        stats["team_size"] = len(current_user.subordinates)
    else:
        stats["tasks"] = len(current_user.assigned_tasks)
        stats["manager_name"] = current_user.manager.name if current_user.manager else None

    return render_template("profile/view.html", person=current_user, stats=stats)


@profile_bp.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    """Lets the logged-in user update their own bio/description."""
    bio = request.form.get("bio", "").strip()
    current_user.bio = bio
    db.session.commit()
    flash("Your profile description was updated.")
    return redirect(url_for("profile.view_profile"))