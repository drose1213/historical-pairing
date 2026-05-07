from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True, pool_recycle=280)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _upgrade_schema()


def _upgrade_schema() -> None:
    """Apply tiny compatibility migrations for databases created before models changed."""
    inspector = inspect(engine)
    if not inspector.has_table("games"):
        return

    game_columns = {column["name"] for column in inspector.get_columns("games")}
    statements: list[str] = []
    if "final_score" not in game_columns:
        statements.append("ALTER TABLE games ADD COLUMN final_score FLOAT NULL")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
