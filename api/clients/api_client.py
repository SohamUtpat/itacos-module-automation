"""Thin wrapper around Playwright's APIRequestContext."""


class ApiClient:
    def __init__(self, request_context, default_headers=None):
        self.request = request_context
        # Stored so tests can confirm the header is configured without
        # reading it back out of a response or a log.
        self.default_headers = dict(default_headers or {})

    def post(self, path, payload):
        return self.request.post(path, data=payload)

    def get(self, path):
        return self.request.get(path)
