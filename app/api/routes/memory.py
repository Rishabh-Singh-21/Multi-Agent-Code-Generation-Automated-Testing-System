from fastapi import APIRouter, Depends, status

from app.schemas.memory import MemoryRecord, MemoryWriteRequest
from app.services.memory_service import MemoryService
from app.utils.dependencies import get_memory_service

router = APIRouter()


@router.post("", response_model=MemoryRecord, status_code=status.HTTP_201_CREATED)
async def write_memory(
    payload: MemoryWriteRequest,
    memory_service: MemoryService = Depends(get_memory_service),
) -> MemoryRecord:
    return await memory_service.write(payload)


@router.get("/{agent_id}", response_model=list[MemoryRecord])
async def read_memory(
    agent_id: str,
    memory_service: MemoryService = Depends(get_memory_service),
) -> list[MemoryRecord]:
    return await memory_service.read(agent_id)
