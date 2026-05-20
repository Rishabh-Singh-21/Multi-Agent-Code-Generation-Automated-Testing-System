from fastapi import APIRouter, Depends, status

from app.schemas.agent import AgentExecutionRequest, AgentExecutionResponse
from app.services.orchestrator import AgentOrchestrator
from app.utils.dependencies import get_orchestrator

router = APIRouter()


@router.post(
    "/execute",
    response_model=AgentExecutionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_agent(
    payload: AgentExecutionRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
) -> AgentExecutionResponse:
    return await orchestrator.execute(payload)
