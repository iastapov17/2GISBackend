from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Запуск Доступ.City API...")
    print(f"📍 Документация доступна: http://localhost:8000/docs")
    
    yield
    
    print("👋 Остановка API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API для построения доступных и тихих маршрутов",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Dostup.City API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

