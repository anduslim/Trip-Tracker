from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.jobs.scheduler import shutdown_scheduler, start_scheduler
from app.routers import auth, flights, health, holidays, notifications, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        shutdown_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Trip Price Tracker API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(holidays.router, prefix="/api/holidays", tags=["holidays"])
    app.include_router(flights.router, tags=["flights"])
    app.include_router(search.router)
    app.include_router(notifications.router)

    return app


app = create_app()
