from pydantic import BaseModel, Field


class AgentExecutionRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)


class AgentExecutionResponse(BaseModel):
    agent_id: str
    status: str
    output: str
