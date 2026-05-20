from datetime import datetime

from pydantic import BaseModel, Field


class MemoryWriteRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    key: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)


class MemoryRecord(BaseModel):
    agent_id: str
    key: str
    value: str
    timestamp: datetime
