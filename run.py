

from flask import redirect, url_for
from app_init import create_app

app = create_app()


@app.route("/")
def home():
    return redirect(url_for("dashboard.index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)