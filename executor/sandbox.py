from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import docker
from docker.errors import DockerException
from configs.settings import settings


@dataclass
class ExecutionResult:
    passed: bool
    stdout: str
    stderr: str
    coverage: str


class DockerSandboxExecutor:
    def __init__(self) -> None:
        self.client = docker.from_env()

    def run_tests(self, session_path: Path) -> ExecutionResult:
        command = "sh -lc 'pip install -q pytest coverage && coverage run -m pytest -q && coverage report -m'"
        try:
            container = self.client.containers.run(
                image=settings.docker_image,
                command=command,
                working_dir="/workspace",
                volumes={str(session_path.resolve()): {"bind": "/workspace", "mode": "rw"}},
                network_disabled=True,
                detach=True,
                mem_limit="512m",
                pids_limit=128,
                security_opt=["no-new-privileges"],
            )
            status = container.wait(timeout=settings.docker_timeout_seconds)
            logs = container.logs(stdout=True, stderr=False).decode("utf-8", errors="ignore")
            errs = container.logs(stdout=False, stderr=True).decode("utf-8", errors="ignore")
            container.remove(force=True)
            passed = int(status.get("StatusCode", 1)) == 0
            coverage_line = next((l for l in logs.splitlines() if "TOTAL" in l), "TOTAL 0 0 0%")
            return ExecutionResult(passed=passed, stdout=logs, stderr=errs, coverage=coverage_line)
        except DockerException as exc:
            return ExecutionResult(False, "", f"Docker error: {exc}", "TOTAL 0 0 0%")
