from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core import engine, Base

from src.users import User
from src.services import Service
from src.providers import Provider
from src.bookings import Booking
from src.availability import Availability
from src.chat import ChatLog

from src.users import users_router
from src.services import services_router
from src.providers import providers_router
from src.bookings import bookings_router
from src.availability import availability_router
from src.chat import chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


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

