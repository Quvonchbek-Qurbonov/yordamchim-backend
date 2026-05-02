from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from redis import Redis

from src.core import engine, Base
from src.core.config import settings

from src.users import User
from src.services import Service
from src.providers import Profile, ProviderService
from src.bookings import Booking
from src.availability import Availability
from src.chat import ChatLog

from src.users import users_router
from src.services import services_router
from src.providers import providers_router
from src.bookings import bookings_router
from src.availability import availability_router
from src.chat import chat_router
from src.auth import auth_router
from src.assets import assets_router


from contextlib import asynccontextmanager
from redis.asyncio import Redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await redis_client.ping()
    except Exception:
        raise
    app.state.redis = redis_client
    try:
        yield
    finally:
        await redis_client.close()

app = FastAPI(
    title="Yordamchim Backend",
    description="API for booking daily need services to save time",
    version="1.0.0",
    lifespan=lifespan
)

# Routes
app.include_router(users_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(providers_router, prefix="/api/v1")
app.include_router(bookings_router, prefix="/api/v1")
app.include_router(availability_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")

