import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "library.db")


class Config:
    BASE_DIR = BASE_DIR
    DATABASE = DATABASE_PATH
    SECRET_KEY = "change-this-secret-key-in-production"
