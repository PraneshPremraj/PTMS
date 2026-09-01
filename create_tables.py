

from app_init import create_app
from extensions import db
import models  # noqa: F401  (import needed so SQLAlchemy knows about the User model)

app = create_app()

with app.app_context():
    db.create_all()
    print("Tables created successfully. Check ptms_db in MySQL Workbench.")