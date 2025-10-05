from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.schemas.routing import Location
from app.schemas.map_layers import LayerType


class ReportData(BaseModel):
    snow_cleared: Optional[bool] = None
    noise_db: Optional[float] = None
    crowd_level: Optional[int] = Field(None, ge=1, le=5)
    light_lux: Optional[int] = None
    has_puddles: Optional[bool] = None
    photo_base64: Optional[str] = Field(None, description="Фото в base64 (опционально)")
    description: Optional[str] = Field(None, max_length=500)


class DeviceData(BaseModel):
    noise_db: Optional[float] = None
    light_lux: Optional[int] = None


class ReportRequest(BaseModel):
    location: Location
    type: LayerType
    data: ReportData
    device: Optional[DeviceData] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": {"lat": 55.755, "lon": 37.617},
                "type": "snow",
                "data": {
                    "snow_cleared": False,
                    "description": "Снег не убран, высота ~15см"
                },
                "device": {
                    "noise_db": 68.5
                }
            }
        }


# ============= RESPONSE SCHEMAS =============

class ReportResponse(BaseModel):
    """Ответ на создание отчёта"""
    report_id: str
    status: str = Field(..., description="accepted/rejected/pending")
    points_earned: int = Field(0, description="Баллы за отчёт (геймификация)")
    message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "report_12345",
                "status": "accepted",
                "points_earned": 5,
                "message": "Спасибо! Ваш отчёт поможет другим пользователям"
            }
        }

