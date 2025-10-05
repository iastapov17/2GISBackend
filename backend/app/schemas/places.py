from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class AccessibilityFilter(str, Enum):
    WHEELCHAIR_ACCESS = "wheelchair_access"
    ACCESSIBLE_PARKING = "accessible_parking"
    ACCESSIBLE_TOILET = "accessible_toilet"
    SERVICE_DOG_FRIENDLY = "service_dog_friendly"
    LOW_NOISE = "low_noise"
    LOW_LIGHT = "low_light"
    LOW_CROWD = "low_crowd"
    BRAILLE_OR_AUDIO = "braille_or_audio"
    HEARING_LOOP = "hearing_loop"


class AccessibilityCondition(BaseModel):
    filter_type: AccessibilityFilter
    name: str = Field(..., description="Название условия")
    rating: float = Field(..., ge=0, le=5, description="Рейтинг качества (0-5)")


class Review(BaseModel):
    id: str
    author: str = Field(..., description="Автор отзыва")
    rating: int = Field(..., ge=1, le=5, description="Оценка от 1 до 5")
    text: str = Field(..., description="Текст отзыва")
    date: datetime = Field(..., description="Дата отзыва")


class PlaceLocation(BaseModel):
    latitude: float = Field(..., description="Широта")
    longitude: float = Field(..., description="Долгота")


class Place(BaseModel):
    id: str = Field(..., description="Уникальный идентификатор")
    name: str = Field(..., description="Название места")
    location: PlaceLocation = Field(..., description="Локация")
    accessibility_conditions: List[AccessibilityCondition] = Field(
        ..., description="Доступные условия и их рейтинги"
    )
    reviews: List[Review] = Field(default_factory=list, description="Отзывы")
    overall_rating: float = Field(..., ge=0, le=5, description="Общий рейтинг")


class PlaceSearchRequest(BaseModel):
    query: str = Field(..., description="Название для поиска")
    location: PlaceLocation = Field(..., description="Локация пользователя")
    filters: List[AccessibilityFilter] = Field(
        default_factory=list, 
        description="Фильтры доступности"
    )


class PlaceSearchResponse(BaseModel):
    places: List[Place] = Field(..., description="Найденные места")
    
    class Config:
        json_schema_extra = {
            "example": {
                "places": [
                    {
                        "id": "place_001",
                        "name": "Кафе 'Уютное место'",
                        "location": {
                            "latitude": 55.7558,
                            "longitude": 37.6173
                        },
                        "accessibility_conditions": [
                            {
                                "filter_type": "wheelchair_access",
                                "name": "Пандус или лифт",
                                "rating": 4.5
                            }
                        ],
                        "reviews": [
                            {
                                "id": "review_001",
                                "author": "Анна С.",
                                "rating": 5,
                                "text": "Отличное место, очень доступно!",
                                "date": "2025-01-15T10:30:00Z"
                            }
                        ],
                        "overall_rating": 4.8
                    }
                ]
            }
        }


class AccessibilityRating(BaseModel):
    filter_type: AccessibilityFilter = Field(..., description="Тип фильтра доступности")
    rating: float = Field(..., ge=0, le=5, description="Рейтинг от 0 до 5")


class AddReviewRequest(BaseModel):
    place_id: str = Field(..., description="ID места")
    accessibility_ratings: List[AccessibilityRating] = Field(..., description="Рейтинги доступности")
    text: str = Field(..., min_length=1, max_length=1000, description="Текст отзыва")
    author: str = Field(..., min_length=2, max_length=50, description="Автор отзыва")
    overall_rating: int = Field(..., ge=1, le=5, description="Общий рейтинг от 1 до 5")
    
    class Config:
        json_schema_extra = {
            "example": {
                "place_id": "70000001234567",
                "accessibility_ratings": [
                    {
                        "filter_type": "wheelchair_access",
                        "rating": 4.5
                    },
                    {
                        "filter_type": "low_noise",
                        "rating": 3.0
                    }
                ],
                "text": "Отличное место! Есть пандус, но немного шумно.",
                "author": "Анна С.",
                "overall_rating": 4
            }
        }


