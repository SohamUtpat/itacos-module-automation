import re
from urllib.parse import urlparse


def url_is(path: str):
    """Match app URLs that sometimes include a trailing space."""
    return re.compile(rf".*{re.escape(path)}\s*$")


def path_matches(url: str, path: str) -> bool:
    """True when the URL path equals path (ignores query/hash; trims trailing /)."""
    current = (urlparse(url).path or "").rstrip("/")
    return current == path.rstrip("/")
