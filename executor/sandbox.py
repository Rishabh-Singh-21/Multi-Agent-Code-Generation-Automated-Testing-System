from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tarfile
import tempfile
import time
from io import BytesIO
from typing import Any

import docker

from configs.settings import settings


@dataclass
class ExecutionResult:
    passed: bool
    stdout: str
    stderr: str
    coverage: str
    exit_code: int
    timed_out: bool
    duration_seconds: float
    blocked_patterns: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "coverage": self.coverage,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "duration_seconds": round(self.duration_seconds, 3),
            "blocked_patterns": self.blocked_patterns,
        }


class SandboxRunner:
    def __init__(self) -> None:
        self.client = docker.from_env()

    @staticmethod
    def _prepare_archive(source_dir: Path) -> bytes:
        archive_stream = BytesIO()
        with tarfile.open(fileobj=archive_stream, mode="w") as tar:
            for path in source_dir.rglob("*"):
                tar.add(path, arcname=path.relative_to(source_dir))
        archive_stream.seek(0)
        return archive_stream.getvalue()

    def run(self, source_dir: Path, command: str, timeout_seconds: int) -> tuple[int, str, str, bool, float]:
        start = time.monotonic()
        container = None
        try:
            container = self.client.containers.create(
                image=settings.docker_image,
                command=["/bin/sh", "-lc", command],
                working_dir="/workspace",
                network_disabled=True,
                read_only=True,
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m", "/workspace": "rw,noexec,nosuid,size=128m"},
                mem_limit="512m",
                memswap_limit="512m",
                pids_limit=128,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                user="65534:65534",
                detach=True,
            )
            container.put_archive("/workspace", self._prepare_archive(source_dir))
            container.start()
            try:
                wait_result = container.wait(timeout=timeout_seconds)
                timed_out = False
            except Exception:
                timed_out = True
                container.kill()
                wait_result = {"StatusCode": 124}

            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="ignore")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="ignore")
            status_code = int(wait_result.get("StatusCode", 1))
            return status_code, stdout, stderr, timed_out, time.monotonic() - start
        finally:
            if container is not None:
                container.remove(force=True)


class SecureExecutor:
    DANGEROUS_PATTERNS = (
        "import os;os.system",
        "subprocess.",
        "socket.",
        "shutil.rmtree(\"/\")",
        "open(\"/etc/passwd\")",
        "__import__('os').system",
    )

    def __init__(self, runner: SandboxRunner) -> None:
        self.runner = runner

    def _scan_for_dangerous_content(self, session_path: Path) -> list[str]:
        blocked: list[str] = []
        for candidate in session_path.rglob("*.py"):
            content = candidate.read_text(encoding="utf-8", errors="ignore")
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern in content and pattern not in blocked:
                    blocked.append(pattern)
        return blocked

    def execute(self, session_path: Path) -> ExecutionResult:
        blocked = self._scan_for_dangerous_content(session_path)
        if blocked:
            return ExecutionResult(
                passed=False,
                stdout="",
                stderr=f"Blocked dangerous patterns: {', '.join(blocked)}",
                coverage="TOTAL 0 0 0%",
                exit_code=126,
                timed_out=False,
                duration_seconds=0.0,
                blocked_patterns=blocked,
            )

        command = "python -m pytest -q --maxfail=1 --disable-warnings"
        code, stdout, stderr, timed_out, duration = self.runner.run(
            source_dir=session_path,
            command=command,
            timeout_seconds=settings.docker_timeout_seconds,
        )
        coverage_line = next((line for line in (stdout + "\n" + stderr).splitlines() if "TOTAL" in line), "TOTAL 0 0 0%")
        return ExecutionResult(
            passed=code == 0,
            stdout=stdout,
            stderr=stderr,
            coverage=coverage_line,
            exit_code=code,
            timed_out=timed_out,
            duration_seconds=duration,
            blocked_patterns=[],
        )


class ExecutionManager:
    def __init__(self) -> None:
        self.executor = SecureExecutor(SandboxRunner())

    def run_tests(self, session_path: Path) -> ExecutionResult:
        isolated_root = Path(tempfile.mkdtemp(prefix="sandbox-run-"))
        try:
            workspace = isolated_root / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            for src in session_path.rglob("*"):
                dst = workspace / src.relative_to(session_path)
                if src.is_dir():
                    dst.mkdir(parents=True, exist_ok=True)
                else:
                    dst.write_bytes(src.read_bytes())
            return self.executor.execute(workspace)
        finally:
            for child in sorted(isolated_root.rglob("*"), reverse=True):
                if child.is_file() or child.is_symlink():
                    child.unlink(missing_ok=True)
                elif child.is_dir():
                    child.rmdir()
            isolated_root.rmdir()


class DockerSandboxExecutor(ExecutionManager):
    pass
