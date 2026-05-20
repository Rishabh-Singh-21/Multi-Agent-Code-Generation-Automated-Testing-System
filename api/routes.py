from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.schemas import RunRequest, RunResponse, AgentEvent
from api.orchestrator import Orchestrator
from memory.database import get_db, SessionRun, AgentLog
from configs.settings import settings

router = APIRouter()


@router.post("/run", response_model=RunResponse)
async def run_workflow(payload: RunRequest, db: Session = Depends(get_db)) -> RunResponse:
    row = SessionRun(prompt=payload.prompt, status="running", session_path="")
    db.add(row)
    db.commit()
    db.refresh(row)
    session_path = Path(settings.generated_root) / f"session_{row.id}"
    session_path.mkdir(parents=True, exist_ok=True)
    row.session_path = str(session_path)
    db.commit()
    try:
        output = Orchestrator().run(db, payload.prompt, payload.max_retries, session_path, row)
        row.status = "completed"
        row.tests_passed = output["passed"]
        row.retries_used = output["retries_used"]
        row.coverage = output["coverage"]
        row.quality_score = str(output["quality_score"])
        db.commit()
        events = db.query(AgentLog).filter(AgentLog.session_id == row.id).all()
        return RunResponse(
            session_id=row.id,
            status=row.status,
            retries_used=row.retries_used,
            tests_passed=row.tests_passed,
            coverage=row.coverage,
            quality_score=float(row.quality_score),
            code=output["code"],
            tests=output["tests"],
            logs=output["logs"],
            events=[AgentEvent(agent=e.agent_name, message=e.message) for e in events],
        )
    except Exception as exc:
        row.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/sessions")
async def list_sessions(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(SessionRun).order_by(SessionRun.id.desc()).all()
    return [{"id": r.id, "status": r.status, "passed": r.tests_passed, "created_at": r.created_at.isoformat()} for r in rows]
