from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.schemas.map_layers import (
    LayerType, 
    AllLayersResponse,
)
from app.services.map_service import MapService

router = APIRouter()
map_service = MapService()


@router.get("/all", response_model=AllLayersResponse)
async def get_all_layers(
    bbox: str = Query(
        ..., 
        description="Bounding box: lat_min,lon_min,lat_max,lon_max",
        example="55.75,37.61,55.76,37.63"
    ),
    layers: Optional[str] = Query(
        None,
        description="Какие слои получить (через запятую): noise,crowd,light,puddles. Если не указано - все",
        example="noise,crowd,light"
    ),
    time: Optional[datetime] = Query(
        None,
        description="Время для прогноза (опционально)"
    )
):
    try:
        coords = [float(x) for x in bbox.split(",")]
        if len(coords) != 4:
            raise ValueError("bbox должен содержать 4 координаты")
        
        lat_min, lon_min, lat_max, lon_max = coords
        
        if layers:
            requested_layers = [LayerType(l.strip()) for l in layers.split(",")]
        else:
            requested_layers = [LayerType.NOISE, LayerType.CROWD, LayerType.LIGHT, LayerType.PUDDLES]
        
        all_layers_data = await map_service.get_all_layers(
            layer_types=requested_layers,
            bbox=(lat_min, lon_min, lat_max, lon_max),
            time=time
        )
        
        return AllLayersResponse(
            updated_at=datetime.utcnow(),
            bbox=bbox,
            layers=all_layers_data
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")
