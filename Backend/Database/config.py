import os

# Get the absolute path to the database file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "socratic.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}" 