from fastapi import APIRouter, HTTPException
from app.schemas.routing import CalmRouteRequest, CalmRouteResponse
from app.services.routing_service import RoutingService
from app.services.calm_route_service import get_calm_route_service

router = APIRouter()
routing_service = RoutingService()
calm_route_service = get_calm_route_service()


@router.post("/calm", response_model=CalmRouteResponse)
async def calculate_calm_route(request: CalmRouteRequest):
    try:
        return await calm_route_service.build_calm_route(request)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка построения маршрута: {str(e)}")

