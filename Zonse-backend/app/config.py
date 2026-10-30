import os


class Settings:
    def __init__(self):
        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "Zonse Homes Backend")
        self.API_V1_STR = os.getenv("API_V1_STR", "/api/v1")
        self.POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "zonse_homes")
        self.POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
        self.SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI") or (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()