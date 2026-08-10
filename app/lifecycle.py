from __future__ import annotations

import signal


class Lifecycle:
    """Giữ trạng thái vòng đời của process."""

    def __init__(self) -> None:
        self.shutting_down = False
        # Handler đã được đăng ký trước ta (của uvicorn) — xem install()
        self._previous: dict = {}

    def install(self):
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._previous[sig] = signal.getsignal(sig)   # nhớ handler cũ
            signal.signal(sig, self.request_shutdown)     # rồi mới ghi đè

    def request_shutdown(self, signum=None, frame=None):
        self.shutting_down = True                         # chỉ bật cờ
        previous = self._previous.get(signum)
        if callable(previous):
            previous(signum, frame)                       # nhường lại cho uvicorn


# Một instance dùng chung cho cả app
lifecycle = Lifecycle()