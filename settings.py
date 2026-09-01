

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings/password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not check_password_hash(current_user.password_hash, current_password):
            flash("Current password is incorrect.")
        elif len(new_password) < 6:
            flash("New password must be at least 6 characters.")
        elif new_password != confirm_password:
            flash("New passwords do not match.")
        else:
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("Password updated successfully.")
            return redirect(url_for("dashboard.index"))

    return render_template("settings/password.html")