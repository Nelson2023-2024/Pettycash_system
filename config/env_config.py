import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Environment:
    def __init__(self):
        # jwt configuration
        self.JWT_ACCESS_SECRET = os.getenv("JWT_ACCESS_SECRET", "secret")
        self.JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", "secret")

        # gmail smtp configuration
        self.EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
        self.EMAIL_HOST = os.getenv("EMAIL_HOST")
        self.EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS")
        self.EMAIL_PORT = os.getenv("EMAIL_PORT")
        self.EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
        self.EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

        # --------docker postgress-----------------------
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB")
        self.POSTGRES_PORT = os.getenv("POSTGRES_PORT")
        self.POSTGRES_HOST = os.getenv("POSTGRES_HOST")


ENV = Environment()
