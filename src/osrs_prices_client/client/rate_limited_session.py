import time
import requests


class RateLimitedSession(requests.Session):
    """Requests Session object that overloads the request method to
    have single-threaded rate limiting"""

    def __init__(self, max_tps: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._min_interval = 1 / max_tps
        self._last = 0.0

    def request(self, *args, **kwargs):
        now = time.time()
        time_to_wait = self._min_interval - (now - self._last)
        if time_to_wait > 0:
            time.sleep(time_to_wait)
        response = super().request(*args, **kwargs)
        self._last = time.time()
        return response
