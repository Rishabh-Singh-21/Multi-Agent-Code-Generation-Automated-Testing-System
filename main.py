from fastapi import FastAPI
from api.routes import router
from memory.database import init_db
from utils.logger import configure_logging
from configs.settings import settings

configure_logging()
init_db()

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
