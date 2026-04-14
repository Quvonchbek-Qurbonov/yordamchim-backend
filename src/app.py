from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core import engine, Base


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
# app.include_router(default.router, prefix="/api/v1")
# app.include_router(api.router, prefix="/api/v1")

