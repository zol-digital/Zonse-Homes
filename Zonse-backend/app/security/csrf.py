from urllib.parse import urlsplit

from fastapi import HTTPException, Request, status

from app.config import settings

_UNSAFE_METHODS = {"DELETE", "PATCH", "POST", "PUT"}


def _origin_from_url(value: str, *, allow_path: bool) -> str | None:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None

    scheme = parsed.scheme.lower()
    if (
        scheme not in {"http", "https"}
        or not parsed.netloc
        or hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.netloc.endswith(":")
        or (not allow_path and parsed.path not in {"", "/"})
    ):
        return None

    hostname = hostname.lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    default_port = 80 if scheme == "http" else 443
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{scheme}://{hostname}{port_suffix}"


def validate_csrf_origin(request: Request) -> None:
    if request.method.upper() not in _UNSAFE_METHODS:
        return

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    source = origin if origin is not None else referer
    if source is None:
        if request.cookies.get(settings.SESSION_COOKIE_NAME):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cross-origin request rejected",
            )
        return

    source_origin = _origin_from_url(source, allow_path=origin is None)
    request_origin = _origin_from_url(str(request.base_url), allow_path=True)
    allowed_origins = set(settings.SESSION_CSRF_TRUSTED_ORIGINS)
    if request_origin is not None:
        allowed_origins.add(request_origin)

    if source_origin is None or source_origin not in allowed_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-origin request rejected",
        )
