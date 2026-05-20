from functools import lru_cache

from app.memory.shared_memory import SharedMemoryStore
from app.services.memory_service import MemoryService
from app.services.orchestrator import AgentOrchestrator


@lru_cache
def get_memory_store() -> SharedMemoryStore:
    return SharedMemoryStore()


@lru_cache
def get_memory_service() -> MemoryService:
    return MemoryService(get_memory_store())


@lru_cache
def get_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()
