from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import db as db_module
from app.db import get_db
from app.main import app
from app.models import Base


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def db(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    # Also patch the module-level SessionLocal in case anything reaches for it directly.
    original_session_local = db_module.SessionLocal
    db_module.SessionLocal = session_factory  # type: ignore[assignment]
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
        db_module.SessionLocal = original_session_local


@pytest_asyncio.fixture
async def authed_client(client: AsyncClient) -> AsyncClient:
    resp = await client.post(
        "/api/auth/register",
        json={"email": "u@example.com", "password": "password123", "display_name": "U"},
    )
    assert resp.status_code == 201, resp.text
    return client
