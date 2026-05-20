from pathlib import Path
from radon.complexity import cc_visit
from sqlalchemy.orm import Session
from agents.base import AgentContext
from agents.agents import PlannerAgent, CodeGeneratorAgent, TestGeneratorAgent, DebugFixAgent, ReflectionAgent
from executor.sandbox import DockerSandboxExecutor
from memory.database import AgentLog, SessionRun
from utils.llm import get_llm_client


class Orchestrator:
    def __init__(self) -> None:
        llm = get_llm_client()
        self.planner = PlannerAgent(llm)
        self.codegen = CodeGeneratorAgent(llm)
        self.testgen = TestGeneratorAgent(llm)
        self.debugger = DebugFixAgent(llm)
        self.reflector = ReflectionAgent(llm)
        self.executor = DockerSandboxExecutor()

    def _log(self, db: Session, session_id: int, agent: str, msg: str) -> None:
        db.add(AgentLog(session_id=session_id, agent_name=agent, message=msg))
        db.commit()

    def run(self, db: Session, prompt: str, max_retries: int, session_path: Path, session_row: SessionRun) -> dict:
        context = AgentContext(prompt=prompt)
        plan = self.planner.run(context)
        self._log(db, session_row.id, self.planner.name, plan)
        code = self.codegen.run(context)
        tests = self.testgen.run(context)
        (session_path / "app").mkdir(parents=True, exist_ok=True)
        (session_path / "tests").mkdir(parents=True, exist_ok=True)
        (session_path / "app" / "__init__.py").write_text("")
        (session_path / "app" / "main.py").write_text(code)
        (session_path / "tests" / "test_main.py").write_text(tests)

        logs = ""
        coverage = "TOTAL 0 0 0%"
        passed = False
        retries_used = 0
        for retry in range(max_retries):
            retries_used = retry
            result = self.executor.run_tests(session_path)
            logs = result.stdout + "\n" + result.stderr
            coverage = result.coverage
            self._log(db, session_row.id, "execution", logs[-2000:])
            if result.passed:
                passed = True
                break
            context.previous_error = logs
            debug_msg = self.debugger.run(context)
            reflection_msg = self.reflector.run(context)
            self._log(db, session_row.id, self.debugger.name, debug_msg)
            self._log(db, session_row.id, self.reflector.name, reflection_msg)
            (session_path / "app" / "main.py").write_text(self.codegen.run(context))

        complexity = sum(block.complexity for block in cc_visit(code)) or 1
        quality_score = max(0.0, 10.0 - (complexity / 2))
        return {
            "passed": passed,
            "coverage": coverage,
            "logs": logs,
            "code": code,
            "tests": tests,
            "retries_used": retries_used,
            "quality_score": quality_score,
        }
