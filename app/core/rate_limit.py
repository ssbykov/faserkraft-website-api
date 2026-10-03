"""
app/core/rate_limit.py
Простой ограничитель частоты в памяти процесса (подходит для одного воркера uvicorn).
"""
import threading
import time
from collections import defaultdict, deque

from starlette.requests import Request

from app.core.config import settings


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_seconds: int) -> None:
        self.max_events = max_events
        self.window = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque:
        q = self._events[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if not q:
            self._events.pop(key, None)
            return deque()
        return q

    def is_limited(self, key: str) -> bool:
        with self._lock:
            return len(self._prune(key, time.monotonic())) >= self.max_events

    def hit(self, key: str) -> None:
        with self._lock:
            now = time.monotonic()
            self._prune(key, now)
            self._events[key].append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)


def client_ip(request: Request) -> str:
    if settings.TRUST_PROXY:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Заявки: сайт ходит в API с сервера Next.js, поэтому IP у всех посетителей одинаковый,
# если TRUST_PROXY выключен. Поэтому есть и лимит на IP, и общий лимит.
leads_ip_limiter = SlidingWindowLimiter(max_events=10, window_seconds=600)
leads_global_limiter = SlidingWindowLimiter(max_events=60, window_seconds=3600)

# Вход в админку: неудачные попытки.
admin_login_limiter = SlidingWindowLimiter(max_events=5, window_seconds=900)
