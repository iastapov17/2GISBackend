from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class LayerType(str, Enum):
    NOISE = "noise"
    CROWD = "crowd"
    LIGHT = "light"
    PUDDLES = "puddles"


class NoiseLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"




class LayerRequest(BaseModel):
    layer_type: LayerType
    bbox: str = Field(..., description="Bounding box: lat_min,lon_min,lat_max,lon_max")
    time: Optional[datetime] = Field(None, description="Время для прогноза (опционально)")


class Geometry(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class SegmentFeature(BaseModel):
    segment_id: str
    geometry: Geometry
    value: float = Field(..., description="Значение метрики (дБ, уровень толпы и т.д.)")
    level: str = Field(..., description="Категория: low/medium/high/extreme")
    color: str = Field(..., description="HEX цвет для отображения")
    street_name: Optional[str] = None
    confidence: float = Field(0.8, ge=0, le=1, description="Уверенность в данных")
    last_updated: Optional[datetime] = None


class LayerResponse(BaseModel):
    """Ответ с данными слоя"""
    layer: LayerType
    updated_at: datetime
    bbox: str
    features: List[SegmentFeature]
    
    class Config:
        json_schema_extra = {
            "example": {
                "layer": "noise",
                "updated_at": "2025-10-04T10:30:00Z",
                "bbox": "55.75,37.61,55.76,37.63",
                "features": [
                    {
                        "segment_id": "segment_001",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[37.617, 55.755], [37.618, 55.755], [37.618, 55.756], [37.617, 55.756], [37.617, 55.755]]]
                        },
                        "value": 72.5,
                        "level": "medium",
                        "color": "#EAB308",
                        "street_name": "ул. Арбат",
                        "confidence": 0.85,
                        "last_updated": "2025-10-04T10:00:00Z"
                    }
                ]
            }
        }


class AllLayersResponse(BaseModel):
    """Ответ со всеми слоями сразу"""
    updated_at: datetime
    bbox: str
    layers: Dict[str, List[SegmentFeature]]  # {"noise": [...], "crowd": [...], ...}
    
    class Config:
        json_schema_extra = {
            "example": {
                "updated_at": "2025-10-04T10:30:00Z",
                "bbox": "55.75,37.61,55.76,37.63",
                "layers": {
                    "noise": [
                        {
                            "segment_id": "segment_001",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [[[37.617, 55.755], [37.618, 55.755], [37.618, 55.756], [37.617, 55.756], [37.617, 55.755]]]
                            },
                            "value": 72.5,
                            "level": "medium",
                            "color": "#EAB308"
                        }
                    ],
                    "crowd": []
                }
            }
        }

