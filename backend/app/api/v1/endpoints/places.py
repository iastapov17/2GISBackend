from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional

from app.schemas.places import (
    PlaceSearchRequest,
    PlaceSearchResponse,
    AccessibilityFilter,
    PlaceLocation,
    AddReviewRequest
)
from app.services.places_service import PlacesService

router = APIRouter()
places_service = PlacesService()


@router.get("/search", response_model=PlaceSearchResponse)
async def search_places(
    query: str = Query(..., description="Название для поиска"),
    latitude: float = Query(..., description="Широта"),
    longitude: float = Query(..., description="Долгота"),
    filters: Optional[str] = Query(None, description="Фильтры доступности через запятую")
):
    try:
        filter_list = []
        if filters:
            filter_strings = [f.strip() for f in filters.split(",")]
            for filter_str in filter_strings:
                try:
                    filter_enum = AccessibilityFilter(filter_str)
                    filter_list.append(filter_enum)
                except ValueError:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Неизвестный фильтр: {filter_str}"
                    )
        
        request = PlaceSearchRequest(
            query=query,
            location=PlaceLocation(
                latitude=latitude,
                longitude=longitude
            ),
            filters=filter_list
        )
        
        result = await places_service.search_places(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска мест: {str(e)}")


@router.post("/reviews", status_code=status.HTTP_204_NO_CONTENT)
async def add_review(request: AddReviewRequest):
    try:
        success = await places_service.add_review(request)
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Ошибка при добавлении отзыва"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при добавлении отзыва: {str(e)}"
        )
