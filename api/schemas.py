from pydantic import BaseModel, Field
from typing import List


class RunRequest(BaseModel):
    prompt: str = Field(min_length=5)
    max_retries: int = Field(default=3, ge=1, le=10)


class AgentEvent(BaseModel):
    agent: str
    message: str


class RunResponse(BaseModel):
    session_id: int
    status: str
    retries_used: int
    tests_passed: bool
    coverage: str
    quality_score: float
    code: str
    tests: str
    logs: str
    events: List[AgentEvent]
