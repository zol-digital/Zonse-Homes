import os

from sqlalchemy.engine import URL


class Settings:
    def __init__(self):
        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "Zonse Homes Backend")
        self.API_V1_STR = os.getenv("API_V1_STR", "/api/v1")
        self.POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "zonse_homes")
        self.POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
        database_uri = os.getenv("SQLALCHEMY_DATABASE_URI")
        if database_uri:
            self.SQLALCHEMY_DATABASE_URI = database_uri
        else:
            self.SQLALCHEMY_DATABASE_URI = URL.create(
                drivername="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=int(self.POSTGRES_PORT),
                database=self.POSTGRES_DB,
            ).render_as_string(hide_password=False)


settings = Settings()