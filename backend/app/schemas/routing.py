from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class RoutePriorities(BaseModel):
    noise: float = Field(0.5, ge=0, le=1, description="Вес шума")
    crowd: float = Field(0.4, ge=0, le=1, description="Вес толпы")
    distance: float = Field(0.1, ge=0, le=1, description="Вес длины маршрута")


class AvoidOptions(BaseModel):
    noise_above_db: Optional[int] = Field(75, description="Избегать шума выше N дБ")
    crowd_level_above: Optional[int] = Field(4, ge=1, le=5, description="Избегать толпы выше уровня")
    puddles: bool = Field(False, description="Избегать луж")
    light_below_lux: Optional[int] = Field(50, description="Избегать освещения ниже N лк")
    stairs: bool = Field(True, description="Избегать лестниц")
    unpaved: bool = Field(False, description="Избегать грунтовых дорог")


class RouteProfile(BaseModel):
    priorities: RoutePriorities = Field(default_factory=RoutePriorities)
    avoid: AvoidOptions = Field(default_factory=AvoidOptions)


class CalmRouteRequest(BaseModel):
    start: Location
    end: Location
    profile: RouteProfile = Field(default_factory=RouteProfile)
    alternatives: int = Field(3, ge=1, le=5, description="Количество альтернатив")

class RouteMetrics(BaseModel):
    """Метрики маршрута"""
    distance_m: int = Field(..., description="Расстояние в метрах")
    duration_min: int = Field(..., description="Время в пути (минуты)")
    avg_noise_db: float = Field(..., description="Средний уровень шума")
    avg_crowd: float = Field(..., ge=1, le=5, description="Средний уровень толпы")


class RouteExplanation(BaseModel):
    """Объяснение участка маршрута"""
    segment: str = Field(..., description="Описание участка")
    reason: str = Field(..., description="Причина выбора/избегания")


class RouteWarning(BaseModel):
    """Предупреждение на маршруте"""
    location: List[float] = Field(..., description="[lon, lat]")
    message: str


class RouteGeometry(BaseModel):
    """GeoJSON геометрия маршрута"""
    type: str = "LineString"
    coordinates: List[List[float]]


class Route(BaseModel):
    """Один вариант маршрута"""
    id: str
    name: str = Field(..., description="Название: 'Самый тихий', 'Быстрый' и т.д.")
    geometry: RouteGeometry
    metrics: RouteMetrics
    calm_score: float = Field(..., ge=0, le=10, description="Оценка спокойствия 0-10")
    explanations: List[RouteExplanation] = []
    warnings: List[RouteWarning] = []


class CalmRouteResponse(BaseModel):
    """Ответ со спокойными маршрутами"""
    routes: List[Route] = Field(..., description="Список доступных маршрутов")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "routes": [
                    {
                        "id": "route_1",
                        "name": "Самый тихий (+3 мин)",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[37.617, 55.755], [37.618, 55.756]]
                        },
                        "metrics": {
                            "distance_m": 1200,
                            "duration_min": 15,
                            "avg_noise_db": 62.5,
                            "avg_crowd": 2.1
                        },
                        "calm_score": 8.7,
                        "explanations": [
                            {
                                "segment": "ул. Арбат, 10-15",
                                "reason": "Обошли проспект — там 78 дБ и нет понижения бордюра"
                            }
                        ],
                        "warnings": []
                    }
                ],
                "generated_at": "2025-10-04T10:30:00Z"
            }
        }

