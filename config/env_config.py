import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Environment:
    def __init__(self):
        self.JWT_ACCESS_SECRET = os.getenv("JWT_SECRET", "secret")
        self.JWT_REFRESH_SECRET = os.getenv("REFRESH_SECRET", "secret")


ENV = Environment()


