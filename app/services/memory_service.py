from app.memory.shared_memory import SharedMemoryStore
from app.schemas.memory import MemoryRecord, MemoryWriteRequest


class MemoryService:
    def __init__(self, store: SharedMemoryStore) -> None:
        self.store = store

    async def write(self, payload: MemoryWriteRequest) -> MemoryRecord:
        record = self.store.create_record(payload.agent_id, payload.key, payload.value)
        return await self.store.write(record)

    async def read(self, agent_id: str) -> list[MemoryRecord]:
        return await self.store.read(agent_id)
