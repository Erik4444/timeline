from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from timeline.config import settings


def _get_engine():
    db_url = settings.database_url
    # Resolve relative path for SQLite
    if db_url.startswith("sqlite:///./"):
        rel = db_url[len("sqlite:///./"):]
        abs_path = Path(rel).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{abs_path}"

    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        echo=False,
    )

    if "sqlite" in db_url:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(conn, _record):
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA synchronous=NORMAL")

    return engine


engine = _get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from timeline.models import event, media, tag, connection, import_job  # noqa
    Base.metadata.create_all(bind=engine)
    _create_fts(engine)


def _create_fts(eng):
    with eng.connect() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
                id UNINDEXED,
                title,
                body,
                location_name,
                content='events',
                content_rowid='rowid'
            )
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS events_ai
            AFTER INSERT ON events BEGIN
                INSERT INTO events_fts(rowid, id, title, body, location_name)
                VALUES (new.rowid, new.id, new.title, new.body, new.location_name);
            END
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS events_ad
            AFTER DELETE ON events BEGIN
                INSERT INTO events_fts(events_fts, rowid, id, title, body, location_name)
                VALUES ('delete', old.rowid, old.id, old.title, old.body, old.location_name);
            END
        """))
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS events_au
            AFTER UPDATE ON events BEGIN
                INSERT INTO events_fts(events_fts, rowid, id, title, body, location_name)
                VALUES ('delete', old.rowid, old.id, old.title, old.body, old.location_name);
                INSERT INTO events_fts(rowid, id, title, body, location_name)
                VALUES (new.rowid, new.id, new.title, new.body, new.location_name);
            END
        """))
        conn.commit()
