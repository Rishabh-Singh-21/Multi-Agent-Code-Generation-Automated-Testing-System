"""Complete CrewAI-based multi-agent orchestration system.

This module wires together specialized agents for planning, code generation,
test generation, execution, debugging/fixing, and reflection.
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task


# ==========================
# Structured logging helpers
# ==========================


def setup_logger(name: str = "agent_orchestrator") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "event": getattr(record, "event", "log"),
                "message": record.getMessage(),
            }
            extra_fields = getattr(record, "extra_fields", None)
            if isinstance(extra_fields, dict):
                payload.update(extra_fields)
            return json.dumps(payload)

    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger


# ==================
# Shared memory type
# ==================


@dataclass
class SharedMemory:
    """Shared context memory used by all agents."""

    user_request: str
    plan: str = ""
    generated_code: str = ""
    generated_tests: str = ""
    execution_result: Dict[str, Any] = field(default_factory=dict)
    failure_analysis: str = ""
    fix_patch: str = ""
    reflection: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)

    def write(self, agent_name: str, key: str, value: Any) -> None:
        setattr(self, key, value)
        self.history.append(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "agent": agent_name,
                "key": key,
                "value_preview": str(value)[:400],
            }
        )

    def snapshot(self) -> Dict[str, Any]:
        return {
            "user_request": self.user_request,
            "plan": self.plan,
            "generated_code": self.generated_code,
            "generated_tests": self.generated_tests,
            "execution_result": self.execution_result,
            "failure_analysis": self.failure_analysis,
            "fix_patch": self.fix_patch,
            "reflection": self.reflection,
            "history": self.history,
        }


# =================
# Prompt templates
# =================

PROMPT_TEMPLATES: Dict[str, str] = {
    "planner": (
        "You are the Planner Agent. Create an implementation plan from the user request. "
        "Return numbered steps, expected files, and acceptance criteria.\n\n"
        "User request:\n{user_request}\n\n"
        "Current shared memory snapshot:\n{memory_snapshot}"
    ),
    "code_generator": (
        "You are the Code Generator Agent. Use the plan and request to produce full production code. "
        "Return only code and file layout guidance.\n\n"
        "Plan:\n{plan}\n\nUser request:\n{user_request}\n\n"
        "Memory:\n{memory_snapshot}"
    ),
    "test_generator": (
        "You are the Test Generator Agent. Create complete tests for the generated code. "
        "Cover happy path, edge cases, and regressions. Return full runnable test code.\n\n"
        "Plan:\n{plan}\n\nGenerated code:\n{generated_code}\n\nMemory:\n{memory_snapshot}"
    ),
    "debug_fix": (
        "You are the Debug/Fix Agent. Analyze execution failures and produce a concrete fix patch. "
        "Include root cause and corrected code snippets.\n\n"
        "Execution result:\n{execution_result}\n\n"
        "Failure analysis:\n{failure_analysis}\n\nMemory:\n{memory_snapshot}"
    ),
    "reflection": (
        "You are the Reflection Agent. Reflect on this run and provide: what worked, what failed, "
        "risk areas, and next improvements.\n\nMemory:\n{memory_snapshot}"
    ),
}


@dataclass
class AgentManager:
    """Manages CrewAI agents, task execution flow, retries, and shared memory."""

    output_dir: Path = Path("artifacts")
    max_retries: int = 3
    logger: logging.Logger = field(default_factory=setup_logger)
    memory: Optional[SharedMemory] = None

    def _build_agent(self, role: str, goal: str, backstory: str) -> Agent:
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
        )

    def _run_task(self, agent: Agent, description: str, expected_output: str) -> str:
        task = Task(description=description, expected_output=expected_output, agent=agent)
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()
        return str(result)

    def _log(self, event: str, message: str, **fields: Any) -> None:
        self.logger.info(message, extra={"event": event, "extra_fields": fields})

    def _write_artifact(self, name: str, content: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / name
        path.write_text(content, encoding="utf-8")
        return path

    def _execute_generated_assets(self) -> Dict[str, Any]:
        """Execution Agent operation: writes artifacts then runs tests."""
        code_path = self._write_artifact("generated_code.py", self.memory.generated_code)
        test_path = self._write_artifact("test_generated_code.py", self.memory.generated_tests)

        cmd = ["python", "-m", "pytest", str(test_path), "-q"]
        started = time.time()
        completed = subprocess.run(cmd, capture_output=True, text=True)
        duration = round(time.time() - started, 3)

        return {
            "command": " ".join(cmd),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "duration_seconds": duration,
            "code_path": str(code_path),
            "test_path": str(test_path),
        }

    def _analyze_failure(self, execution_result: Dict[str, Any]) -> str:
        return (
            "Execution failed.\n"
            f"Return code: {execution_result.get('returncode')}\n"
            f"STDOUT:\n{execution_result.get('stdout', '')}\n"
            f"STDERR:\n{execution_result.get('stderr', '')}\n"
            "Likely causes: import mismatch, assertion errors, runtime exceptions, or incomplete code generation."
        )

    def run(self, user_request: str) -> Dict[str, Any]:
        self.memory = SharedMemory(user_request=user_request)
        self._log("start", "Starting multi-agent orchestration", user_request=user_request)

        planner = self._build_agent(
            role="Planner Agent",
            goal="Create a precise implementation plan",
            backstory="Expert software architect translating user intent into actionable execution steps.",
        )
        code_generator = self._build_agent(
            role="Code Generator Agent",
            goal="Generate complete production-ready source code",
            backstory="Senior software engineer specializing in robust code generation.",
        )
        test_generator = self._build_agent(
            role="Test Generator Agent",
            goal="Create comprehensive runnable automated tests",
            backstory="QA engineer focused on coverage, edge cases, and regression prevention.",
        )
        debug_fixer = self._build_agent(
            role="Debug/Fix Agent",
            goal="Find root causes and produce concrete fixes",
            backstory="Expert debugger skilled in resolving failing test suites quickly.",
        )
        reflection = self._build_agent(
            role="Reflection Agent",
            goal="Summarize learning and improvement actions",
            backstory="Continuous-improvement specialist for AI software workflows.",
        )

        # Planner
        plan_prompt = PROMPT_TEMPLATES["planner"].format(
            user_request=user_request,
            memory_snapshot=json.dumps(self.memory.snapshot(), indent=2),
        )
        plan = self._run_task(planner, plan_prompt, "A complete numbered implementation plan.")
        self.memory.write("Planner Agent", "plan", plan)
        self._log("planner_complete", "Planner completed", plan_preview=plan[:300])

        # Initial code + tests
        code_prompt = PROMPT_TEMPLATES["code_generator"].format(
            plan=self.memory.plan,
            user_request=user_request,
            memory_snapshot=json.dumps(self.memory.snapshot(), indent=2),
        )
        code = self._run_task(code_generator, code_prompt, "Full runnable source code.")
        self.memory.write("Code Generator Agent", "generated_code", code)

        test_prompt = PROMPT_TEMPLATES["test_generator"].format(
            plan=self.memory.plan,
            generated_code=self.memory.generated_code,
            memory_snapshot=json.dumps(self.memory.snapshot(), indent=2),
        )
        tests = self._run_task(test_generator, test_prompt, "Full runnable test suite.")
        self.memory.write("Test Generator Agent", "generated_tests", tests)

        self._log("generation_complete", "Code and tests generated")

        # Execution + retry loop
        for attempt in range(1, self.max_retries + 1):
            self._log("execution_attempt", "Running execution agent", attempt=attempt)
            result = self._execute_generated_assets()
            self.memory.write("Execution Agent", "execution_result", result)

            if result["returncode"] == 0:
                self._log("execution_success", "Execution succeeded", attempt=attempt)
                break

            analysis = self._analyze_failure(result)
            self.memory.write("Execution Agent", "failure_analysis", analysis)
            self._log("execution_failure", "Execution failed", attempt=attempt, returncode=result["returncode"])

            fix_prompt = PROMPT_TEMPLATES["debug_fix"].format(
                execution_result=json.dumps(result, indent=2),
                failure_analysis=analysis,
                memory_snapshot=json.dumps(self.memory.snapshot(), indent=2),
            )
            fix = self._run_task(debug_fixer, fix_prompt, "Root-cause analysis and corrected code patch.")
            self.memory.write("Debug/Fix Agent", "fix_patch", fix)

            # Simple integration strategy: append fix notes to code for next iteration context
            self.memory.generated_code = f"{self.memory.generated_code}\n\n# --- Debug/Fix Patch Notes ---\n{fix}"
            self._write_artifact("generated_code.py", self.memory.generated_code)

        reflection_prompt = PROMPT_TEMPLATES["reflection"].format(
            memory_snapshot=json.dumps(self.memory.snapshot(), indent=2)
        )
        reflection_text = self._run_task(reflection, reflection_prompt, "Post-run reflection and improvements.")
        self.memory.write("Reflection Agent", "reflection", reflection_text)

        self._write_artifact("shared_memory_snapshot.json", json.dumps(self.memory.snapshot(), indent=2))
        self._log("complete", "Orchestration completed")
        return self.memory.snapshot()


def main() -> None:
    request = (
        "Build a calculator module with add/subtract/multiply/divide and comprehensive tests. "
        "Ensure divide handles zero division."
    )

    manager = AgentManager(max_retries=3)
    try:
        result = manager.run(request)
        print(json.dumps({"status": "ok", "history_events": len(result["history"])}, indent=2))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
