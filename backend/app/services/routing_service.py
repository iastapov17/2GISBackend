from typing import List, Tuple
import httpx
from datetime import datetime

from app.schemas.routing import (
    CalmRouteRequest,
    Route,
    RouteMetrics,
    RouteExplanation,
    RouteWarning,
    RouteGeometry
)
from app.core.config import settings
from app.data.mock_data import MockDataGenerator


class RoutingService:
    
    def __init__(self):
        self.mock_generator = MockDataGenerator()
    
    async def calculate_calm_routes(
        self, 
        request: CalmRouteRequest
    ) -> List[Route]:
        
        base_routes = await self._get_base_routes(request)
        
        calm_routes = []
        for idx, base_route in enumerate(base_routes):
            metrics, calm_score = self._evaluate_route(
                base_route,
                request.profile.priorities.model_dump()
            )
            
            explanations = self._generate_explanations(
                base_route,
                request.profile.avoid.model_dump()
            )
            
            warnings = self._generate_warnings(base_route)
            
            name = self._generate_route_name(idx, calm_score, metrics)
            
            route = Route(
                id=f"route_{idx + 1}",
                name=name,
                geometry=RouteGeometry(
                    type="LineString",
                    coordinates=base_route["geometry"]["coordinates"]
                ),
                metrics=metrics,
                calm_score=round(calm_score, 1),
                explanations=explanations,
                warnings=warnings
            )
            calm_routes.append(route)
        
        calm_routes.sort(key=lambda r: r.calm_score, reverse=True)
        
        return calm_routes[:request.alternatives]
    
    async def _get_base_routes(
        self, 
        request: CalmRouteRequest
    ) -> List[dict]:
        return self.mock_generator.generate_mock_routes(
            start=(request.start.lat, request.start.lon),
            end=(request.end.lat, request.end.lon),
            count=3
        )
    
    def _evaluate_route(
        self, 
        route: dict,
        priorities: dict
    ) -> Tuple[RouteMetrics, float]:
        segments = self._split_route_to_segments(route)
        
        total_noise = 0
        total_crowd = 0
        
        for segment in segments:
            total_noise += segment["metrics"]["noise_db"]
            total_crowd += segment["metrics"]["crowd_level"]
        
        n = len(segments)
        avg_noise = total_noise / n if n > 0 else 60
        avg_crowd = total_crowd / n if n > 0 else 2.5
        
        distance_m = route.get("distance_m", 1000)
        duration_min = route.get("duration_min", 12)
        
        metrics = RouteMetrics(
            distance_m=distance_m,
            duration_min=duration_min,
            avg_noise_db=round(avg_noise, 1),
            avg_crowd=round(avg_crowd, 1)
        )
        
        calm_score = self._calculate_calm_score(
            metrics,
            priorities
        )
        
        return metrics, calm_score
    
    def _calculate_calm_score(
        self, 
        metrics: RouteMetrics,
        priorities: dict
    ) -> float:
        noise_score = max(0, 10 - (metrics.avg_noise_db - 40) / 5)
        crowd_score = 10 - (metrics.avg_crowd - 1) * 2.5
        
        distance_score = max(0, 10 - (metrics.distance_m - 1000) / 100)
        
        calm_score = (
            noise_score * priorities.get("noise", 0.5) +
            crowd_score * priorities.get("crowd", 0.4) +
            distance_score * priorities.get("distance", 0.1)
        ) * 10
        
        return min(10, max(0, calm_score))
    
    def _split_route_to_segments(self, route: dict) -> List[dict]:
        return route.get("segments", [])
    
    def _generate_explanations(
        self, 
        route: dict,
        avoid_options: dict
    ) -> List[RouteExplanation]:
        explanations = []
        segments = route.get("segments", [])
        
        for segment in segments:
            metrics = segment["metrics"]
            
            if metrics["noise_db"] > avoid_options.get("noise_above_db", 75):
                explanations.append(RouteExplanation(
                    segment=segment.get("street_name", "участок"),
                    reason=f"Обошли — там {int(metrics['noise_db'])} дБ"
                ))
            
            if metrics["crowd_level"] >= avoid_options.get("crowd_level_above", 4):
                explanations.append(RouteExplanation(
                    segment=segment.get("street_name", "участок"),
                    reason="Обошли — там слишком людно"
                ))
        
        return explanations[:3]
    
    def _generate_warnings(self, route: dict) -> List[RouteWarning]:
        warnings = []
        segments = route.get("segments", [])
        
        for segment in segments:
            metrics = segment["metrics"]
            
            if metrics.get("puddles", False):
                coords = segment["geometry"]["coordinates"][0]
                warnings.append(RouteWarning(
                    location=coords,
                    message="Возможны лужи"
                ))
        
        return warnings[:5]
    
    def _generate_route_name(
        self, 
        index: int, 
        calm_score: float,
        metrics: RouteMetrics
    ) -> str:
        if index == 0:
            time_diff = metrics.duration_min - 10
            if time_diff > 0:
                return f"Самый тихий (+{time_diff} мин)"
            else:
                return "Самый тихий"
        elif calm_score > 7:
            return "Спокойный"
        elif calm_score > 5:
            return "Обычный"
        else:
            return "Быстрый (шумно)"

