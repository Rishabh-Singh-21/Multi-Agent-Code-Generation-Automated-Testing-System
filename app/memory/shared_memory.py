import asyncio
from collections import defaultdict
from datetime import datetime, timezone

from app.schemas.memory import MemoryRecord


class SharedMemoryStore:
    def __init__(self) -> None:
        self._store: dict[str, list[MemoryRecord]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def write(self, record: MemoryRecord) -> MemoryRecord:
        async with self._lock:
            self._store[record.agent_id].append(record)
            return record

    async def read(self, agent_id: str) -> list[MemoryRecord]:
        async with self._lock:
            return list(self._store.get(agent_id, []))

    @staticmethod
    def create_record(agent_id: str, key: str, value: str) -> MemoryRecord:
        return MemoryRecord(
            agent_id=agent_id,
            key=key,
            value=value,
            timestamp=datetime.now(timezone.utc),
        )
