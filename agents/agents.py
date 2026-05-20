from agents.base import AgentContext, BaseAgent


class PlannerAgent(BaseAgent):
    name = "planner"

    def run(self, context: AgentContext) -> str:
        return (
            "Plan: Build modular python package with target function in app/main.py, "
            "unit tests in tests/test_main.py, include edge cases and docstrings."
        )


class CodeGeneratorAgent(BaseAgent):
    name = "code_generator"

    def run(self, context: AgentContext) -> str:
        return '''def solve(values: list[int]) -> dict[str, float]:
    """Return summary stats for a list of integers."""
    if not values:
        raise ValueError("values must not be empty")
    total = sum(values)
    return {"total": float(total), "avg": total / len(values), "max": float(max(values)), "min": float(min(values))}
'''


class TestGeneratorAgent(BaseAgent):
    name = "test_generator"

    def run(self, context: AgentContext) -> str:
        return '''from app.main import solve
import pytest

def test_solve_success():
    result = solve([1,2,3])
    assert result["total"] == 6.0
    assert result["avg"] == 2.0
    assert result["max"] == 3.0
    assert result["min"] == 1.0

def test_empty_values():
    with pytest.raises(ValueError):
        solve([])
'''


class DebugFixAgent(BaseAgent):
    name = "debug_fix"

    def run(self, context: AgentContext) -> str:
        return "Adjusted implementation based on error trace: " + context.previous_error[:300]


class ReflectionAgent(BaseAgent):
    name = "reflection"

    def run(self, context: AgentContext) -> str:
        return "Reflection: preserve strict types, handle empty inputs, align tests and implementation."
