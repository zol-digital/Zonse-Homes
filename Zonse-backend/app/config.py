import os
import re
from urllib.parse import urlsplit

from sqlalchemy.exc import ArgumentError
from sqlalchemy.engine import URL, make_url


class Settings:
    def __init__(self):
        self.PROJECT_NAME = os.getenv("PROJECT_NAME", "Zonse Homes Backend")
        self.API_V1_STR = os.getenv("API_V1_STR", "/api/v1")
        self.POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.POSTGRES_DB = os.getenv("POSTGRES_DB", "zonse_homes")
        self.POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
        self.SESSION_COOKIE_NAME = os.getenv(
            "SESSION_COOKIE_NAME", "zonse_session"
        ).strip()
        if not re.fullmatch(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", self.SESSION_COOKIE_NAME):
            raise ValueError("SESSION_COOKIE_NAME must be a valid cookie name")

        try:
            self.SESSION_LIFETIME_SECONDS = int(
                os.getenv("SESSION_LIFETIME_SECONDS", "86400")
            )
        except ValueError:
            raise ValueError("SESSION_LIFETIME_SECONDS must be an integer") from None
        if self.SESSION_LIFETIME_SECONDS <= 0:
            raise ValueError("SESSION_LIFETIME_SECONDS must be positive")

        same_site = os.getenv("SESSION_COOKIE_SAMESITE", "lax").strip().lower()
        if same_site not in {"lax", "strict", "none"}:
            raise ValueError("SESSION_COOKIE_SAMESITE must be lax, strict, or none")
        self.SESSION_COOKIE_SAMESITE = same_site

        secure_setting = os.getenv("SESSION_COOKIE_SECURE")
        if secure_setting is None or not secure_setting.strip():
            self.SESSION_COOKIE_SECURE = self.ENVIRONMENT == "production"
        else:
            normalized_secure = secure_setting.strip().lower()
            if normalized_secure not in {"true", "false", "1", "0", "yes", "no"}:
                raise ValueError("SESSION_COOKIE_SECURE must be a boolean")
            self.SESSION_COOKIE_SECURE = normalized_secure in {"true", "1", "yes"}
        if self.ENVIRONMENT == "production" and not self.SESSION_COOKIE_SECURE:
            raise ValueError("Session cookies must be Secure in production")
        if same_site == "none" and not self.SESSION_COOKIE_SECURE:
            raise ValueError("SameSite=None requires a Secure session cookie")

        trusted_origins = os.getenv("SESSION_CSRF_TRUSTED_ORIGINS", "")
        self.SESSION_CSRF_TRUSTED_ORIGINS = tuple(
            self._validate_origin(origin.strip())
            for origin in trusted_origins.split(",")
            if origin.strip()
        )

        database_uri = os.getenv("SQLALCHEMY_DATABASE_URI")
        if database_uri:
            self.SQLALCHEMY_DATABASE_URI = database_uri
        else:
            if self.ENVIRONMENT == "production":
                required_database_settings = {
                    "POSTGRES_SERVER": self.POSTGRES_SERVER,
                    "POSTGRES_USER": self.POSTGRES_USER,
                    "POSTGRES_PASSWORD": self.POSTGRES_PASSWORD,
                    "POSTGRES_DB": self.POSTGRES_DB,
                }
                missing_settings = [
                    name
                    for name in required_database_settings
                    if not os.getenv(name, "").strip()
                ]
                if missing_settings:
                    raise ValueError(
                        "Production requires explicit database settings: "
                        + ", ".join(missing_settings)
                    )
                if (
                    self.POSTGRES_SERVER.lower() == "localhost"
                    or self.POSTGRES_USER.lower() == "postgres"
                    or self.POSTGRES_PASSWORD
                    in {
                        "postgres",
                        "zonse_password",
                        "replace_with_a_local_password",
                    }
                ):
                    raise ValueError(
                        "Production database settings must not use development defaults"
                    )
            self.SQLALCHEMY_DATABASE_URI = URL.create(
                drivername="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=int(self.POSTGRES_PORT),
                database=self.POSTGRES_DB,
            ).render_as_string(hide_password=False)
        if self.ENVIRONMENT == "production" and database_uri:
            try:
                parsed_database_uri = make_url(database_uri)
            except (ArgumentError, ValueError):
                raise ValueError(
                    "SQLALCHEMY_DATABASE_URI must be valid in production"
                ) from None
            password = parsed_database_uri.password
            if not password or password.strip().lower() in {
                "postgres",
                "zonse_password",
                "replace_with_a_local_password",
            }:
                raise ValueError(
                    "Production database settings must not use development defaults"
                )

    @staticmethod
    def _validate_origin(origin: str) -> str:
        parsed = urlsplit(origin)
        try:
            hostname = parsed.hostname
            port = parsed.port
        except ValueError:
            raise ValueError(
                "SESSION_CSRF_TRUSTED_ORIGINS contains an invalid origin"
            ) from None
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or hostname is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.netloc.endswith(":")
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("SESSION_CSRF_TRUSTED_ORIGINS contains an invalid origin")
        normalized_host = hostname.lower()
        if ":" in normalized_host:
            normalized_host = f"[{normalized_host}]"
        scheme = parsed.scheme.lower()
        default_port = 80 if scheme == "http" else 443
        port_suffix = f":{port}" if port is not None and port != default_port else ""
        return f"{scheme}://{normalized_host}{port_suffix}"


settings = Settings()