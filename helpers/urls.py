import re


def url_is(path: str):
    """Match app URLs that sometimes include a trailing space."""
    return re.compile(rf".*{re.escape(path)}\s*$")
