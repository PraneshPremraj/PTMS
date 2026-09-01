import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:pranesh1407@localhost/ptms_db"

    # Turns off a feature we don't need; keeps things clean
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    
    SECRET_KEY = "dev-secret-key-change-later"

    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  
    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif",
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        "txt", "zip",
    }
   