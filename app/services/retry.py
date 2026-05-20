import asyncio
from collections.abc import Awaitable, Callable


class RetryEngine:
    def __init__(self, attempts: int, base_delay: float) -> None:
        self.attempts = attempts
        self.base_delay = base_delay

    async def run(self, operation: Callable[[], Awaitable[str]]) -> str:
        last_exc: Exception | None = None
        for attempt in range(1, self.attempts + 1):
            try:
                return await operation()
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < self.attempts:
                    await asyncio.sleep(self.base_delay * attempt)
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Retry engine failed without exception")
