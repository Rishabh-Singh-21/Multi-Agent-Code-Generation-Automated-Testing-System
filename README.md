# Multi-Agent Code Generation + Automated Testing System

Production-grade autonomous workflow using FastAPI + Streamlit + multi-agent orchestration with Docker sandboxed test execution.

## Architecture
- **Planner Agent**: parses prompt and sets plan
- **Code Generator Agent**: creates implementation
- **Test Generator Agent**: creates pytest tests
- **Execution Agent**: runs tests in isolated Docker container with timeout/resource limits
- **Debug/Fix Agent**: interprets failures and attempts fixes
- **Reflection Agent**: stores iterative lessons in logs/history

## Folder Structure
- `agents/` agent abstractions and implementations
- `api/` schemas, orchestration, routes
- `frontend/` Streamlit dashboard
- `executor/` Docker sandbox runner
- `memory/` SQLite models and persistence
- `utils/` logging + LLM provider abstraction
- `configs/` environment configuration
- `docker/` service Dockerfiles
- `generated_sessions/` generated code/tests per run
- `logs/` runtime logs
- `tests/` automated checks

## Features Implemented
- Multi-agent orchestration
- Shared context and agent communication logs
- Retry loop with debug + reflection cycle
- Docker-isolated execution with timeout, strict memory/PID limits, read-only filesystem and restricted networking
- Secure Python sandbox with dangerous-pattern blocking, isolated temp workspaces, and structured execution results
- Test coverage extraction from coverage report
- Code quality scoring using radon complexity
- Session persistence in SQLite
- API routes for run and history
- Streamlit UI with logs, code/test viewers, timeline, downloads, metrics
- Configurable LLM providers (OpenAI, Gemini, Groq) via environment variables

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run (local)
```bash
uvicorn main:app --reload
streamlit run frontend/app.py
```

## Run (docker compose)
```bash
docker compose up --build
```

## Environment Variables (`.env`)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-70b-versatile
DOCKER_IMAGE=macgats-sandbox:latest
DOCKER_TIMEOUT_SECONDS=90
MAX_RETRIES=3
DATABASE_URL=sqlite:///./data/sessions.db
```

## API
- `GET /health`
- `POST /api/run`
- `GET /api/sessions`

## Security Controls
- Docker network disabled during test execution
- Memory and PID limits for sandbox containers
- No-new-privileges security option
- Configurable timeout cutoff

