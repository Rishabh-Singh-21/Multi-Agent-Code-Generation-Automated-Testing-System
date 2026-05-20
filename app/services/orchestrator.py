from app.core.config import get_settings
from app.core.exceptions import BackendError
from app.core.logging import get_logger
from app.schemas.agent import AgentExecutionRequest, AgentExecutionResponse
from app.services.retry import RetryEngine


class AgentOrchestrator:
    def __init__(self) -> None:
        settings = get_settings()
        self.retry_engine = RetryEngine(
            attempts=settings.retry_attempts,
            base_delay=settings.retry_base_delay,
        )
        self.logger = get_logger(__name__)

    async def execute(self, payload: AgentExecutionRequest) -> AgentExecutionResponse:
        self.logger.info("Executing agent", extra={"agent_id": payload.agent_id})

        async def _run() -> str:
            if not payload.prompt.strip():
                raise BackendError("Prompt cannot be empty", status_code=422)
            return f"Processed prompt: {payload.prompt}"

        output = await self.retry_engine.run(_run)
        return AgentExecutionResponse(
            agent_id=payload.agent_id,
            status="completed",
            output=output,
        )
