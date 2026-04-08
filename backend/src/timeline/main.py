import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from timeline.config import settings
from timeline.database import create_tables

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Life Timeline",
        version="0.1.0",
        description="Persönliche Lebenszeitleiste",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup():
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        (settings.data_dir / "media").mkdir(exist_ok=True)
        (settings.data_dir / "media" / "thumbnails").mkdir(exist_ok=True)
        (settings.data_dir / "imports").mkdir(exist_ok=True)
        create_tables()
        logger.info("Timeline backend started")

    from timeline.api.events import router as events_router
    from timeline.api.search import router as search_router
    from timeline.api.imports import router as imports_router
    from timeline.api.tags import router as tags_router
    from timeline.api.health import router as health_router

    prefix = settings.api_prefix
    app.include_router(events_router, prefix=f"{prefix}/events", tags=["events"])
    app.include_router(search_router, prefix=f"{prefix}/search", tags=["search"])
    app.include_router(imports_router, prefix=f"{prefix}/imports", tags=["imports"])
    app.include_router(tags_router, prefix=f"{prefix}/tags", tags=["tags"])
    app.include_router(health_router, prefix=prefix, tags=["health"])

    # Serve media files
    media_dir = settings.data_dir / "media"
    if media_dir.exists():
        app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

    return app


app = create_app()
