from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from configs.settings import settings


class Base(DeclarativeBase):
    pass


class SessionRun(Base):
    __tablename__ = "session_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="running")
    retries_used: Mapped[int] = mapped_column(Integer, default=0)
    tests_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_score: Mapped[str] = mapped_column(String(32), default="0")
    coverage: Mapped[str] = mapped_column(String(32), default="0")
    session_path: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AgentLog(Base):
    __tablename__ = "agent_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, index=True)
    agent_name: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
