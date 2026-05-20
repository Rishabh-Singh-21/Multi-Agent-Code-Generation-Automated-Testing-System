from dataclasses import dataclass
from utils.llm import LLMClient


@dataclass
class AgentContext:
    prompt: str
    language: str = "python"
    framework: str = "fastapi"
    previous_error: str = ""


class BaseAgent:
    name = "base"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def run(self, context: AgentContext) -> str:
        raise NotImplementedError
