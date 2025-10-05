from fastapi import APIRouter

from app.api.v1.endpoints import layers, routing, places


api_router = APIRouter()

api_router.include_router(
    layers.router,
    prefix="/layers",
    tags=["Слои карты"]
)

api_router.include_router(
    routing.router,
    prefix="/routes",
    tags=["Маршрутизация"]
)

api_router.include_router(
    places.router,
    prefix="/places",
    tags=["Поиск мест"]
)

