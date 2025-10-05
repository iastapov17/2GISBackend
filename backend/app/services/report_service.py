"""
Сервис для обработки отчётов пользователей (краудсорсинг)
"""
from datetime import datetime
from uuid import uuid4

from app.schemas.reports import ReportRequest, ReportResponse


class ReportService:
    """Сервис для работы с отчётами"""
    
    def __init__(self):
        # Для хакатона храним в памяти
        # В продакшене - в БД
        self.reports = []
    
    async def create_report(self, request: ReportRequest) -> ReportResponse:
        """
        Создать новый отчёт от пользователя
        """
        report_id = str(uuid4())
        
        # Валидация данных
        self._validate_report(request)
        
        # Сохраняем отчёт
        report = {
            "id": report_id,
            "location": request.location.model_dump(),
            "type": request.type,
            "data": request.data.model_dump(),
            "device": request.device.model_dump() if request.device else None,
            "created_at": datetime.utcnow(),
            "verified": False
        }
        self.reports.append(report)
        
        # Вычисляем баллы (геймификация)
        points = self._calculate_points(request)
        
        # TODO: Обновить данные сегментов в БД на основе отчёта
        # await self._update_segments_from_report(report)
        
        return ReportResponse(
            report_id=report_id,
            status="accepted",
            points_earned=points,
            message="Спасибо! Ваш отчёт поможет другим пользователям"
        )
    
    def _validate_report(self, request: ReportRequest):
        """Валидация данных отчёта"""
        # Проверяем координаты
        if not (-90 <= request.location.lat <= 90):
            raise ValueError("Неверная широта")
        if not (-180 <= request.location.lon <= 180):
            raise ValueError("Неверная долгота")
        
        # Проверяем наличие данных
        data_dict = request.data.model_dump(exclude_none=True)
        if not data_dict:
            raise ValueError("Отчёт не содержит данных")
    
    def _calculate_points(self, request: ReportRequest) -> int:
        """
        Вычислить баллы за отчёт (геймификация)
        
        Критерии:
        - Базовый отчёт: 5 баллов
        - С фото: +3 балла
        - С замерами (дБ, люксы): +2 балла за каждый
        - С описанием: +1 балл
        """
        points = 5  # базовые
        
        # Фото
        if request.data.photo_base64:
            points += 3
        
        # Замеры с устройства
        if request.device:
            if request.device.noise_db is not None:
                points += 2
            if request.device.light_lux is not None:
                points += 2
        
        # Описание
        if request.data.description:
            points += 1
        
        return points

