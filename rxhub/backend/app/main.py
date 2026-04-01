import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import auth, member, requests, refill, admin, resources, payments
from app.tasks.background import run_background_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, launch background tasks."""
    Base.metadata.create_all(bind=engine)
    logger.info("LeadwayHMO RxHub started")

    task = asyncio.create_task(run_background_loop())
    yield
    task.cancel()
    logger.info("LeadwayHMO RxHub shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="PBM Member Self-Service Platform — LeadwayHMO",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting (simple in-memory, replace with Redis in production)
from collections import defaultdict
from time import time

_rate_store: dict[str, list[float]] = defaultdict(list)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time()
    window = 60

    # Clean old entries
    _rate_store[client_ip] = [t for t in _rate_store[client_ip] if now - t < window]

    if len(_rate_store[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Try again shortly."},
        )

    _rate_store[client_ip].append(now)
    return await call_next(request)


# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(member.router, prefix="/api")
app.include_router(requests.router, prefix="/api")
app.include_router(refill.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(payments.router, prefix="/api")


# Serve local uploads during development (when S3 not configured)
_uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
if os.path.isdir(_uploads_dir) or not settings.AWS_ACCESS_KEY_ID:
    os.makedirs(_uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}
