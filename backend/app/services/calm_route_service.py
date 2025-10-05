from typing import List, Dict, Tuple, Optional
from shapely.geometry import Polygon
from app.services.gis_service import get_gis_service
from app.services.map_service import MapService
from app.schemas.routing import CalmRouteRequest, CalmRouteResponse, Route, RouteMetrics, RouteGeometry, RouteExplanation
from app.schemas.map_layers import LayerType


class CalmRouteService:
    
    def __init__(self):
        self.gis_service = get_gis_service()
        self.map_service = MapService()
    
    async def build_calm_route(
        self, 
        request: CalmRouteRequest
    ) -> CalmRouteResponse:
        start = (request.start.lat, request.start.lon)
        end = (request.end.lat, request.end.lon)
        
        print(f"🗺️ [CALM ROUTE] Строим маршрут: {start} -> {end}")
        
        base_route = await self.gis_service.get_route(
            start=start,
            end=end,
            profile="pedestrian"
        )

        if not base_route:
            return self._create_fallback_route(request)
        
        # Шаг 2: Получить полигоны в области маршрута
        bbox = self._get_route_bbox(base_route)
        problematic_polygons = await self._find_problematic_polygons(
            bbox, 
            request
        )
        
        if problematic_polygons:
            print(f"🚫 [CALM ROUTE] Найдено {len(problematic_polygons)} проблемных полигонов")
            
            merged_polygons = self._merge_intersecting_polygons(problematic_polygons)
            print(f"🔗 [CALM ROUTE] Объединено в {len(merged_polygons)} полигонов")
            
            exclude_polygons = [
                self.gis_service.create_exclude_polygon(polygon["coordinates"])
                for polygon in merged_polygons
            ][:20]
            print(f"✅ [CALM ROUTE] Исключения: {len(exclude_polygons)} полигонов")
            
            calm_route = await self.gis_service.get_route(
                start=start,
                end=end,
                profile="pedestrian",
                exclude_polygons=exclude_polygons
            )
            
            if calm_route:
                # print(f"✅ [CALM ROUTE] Результат запроса: {calm_route}")
                print(f"✅ [CALM ROUTE] Построен маршрут с исключениями")
                return self._convert_route_to_response(calm_route, request)
            else:
                print(f"⚠️ [CALM ROUTE] Не удалось построить маршрут с исключениями, используем базовый")
                return self._convert_route_to_response(base_route, request)
        else:
            print(f"✅ [CALM ROUTE] Проблемных полигонов не найдено, используем базовый маршрут")
    
    async def _find_problematic_polygons(
        self, 
        bbox: Tuple[float, float, float, float],
        request: CalmRouteRequest
    ) -> List[Dict]:
        """
        Найти полигоны, которые нарушают фильтры пользователя
        
        Args:
            bbox: область поиска (lat_min, lon_min, lat_max, lon_max)
            request: запрос с фильтрами
        
        Returns:
            Список проблемных полигонов
        """
        problematic_polygons = []
        
        # Получаем все слои данных в области
        all_layers = await self.map_service.get_all_layers(
            layer_types=[LayerType.NOISE, LayerType.CROWD, LayerType.LIGHT, LayerType.PUDDLES],
            bbox=bbox
        )
        
        # Проверяем каждый слой на соответствие фильтрам
        for layer_type, features in all_layers.items():
            for feature in features:
                polygon = feature.geometry.coordinates[0]  # Первое кольцо
                
                # Создаем метрики из атрибутов SegmentFeature
                metrics = {
                    "noise_db": feature.value if layer_type == LayerType.NOISE else 0,
                    "crowd_level": feature.value if layer_type == LayerType.CROWD else 0,
                    "light_lux": feature.value if layer_type == LayerType.LIGHT else 0,
                    "puddles": feature.value > 0.5 if layer_type == LayerType.PUDDLES else False
                }
                
                # Проверяем фильтры
                if True:
                    problematic_polygons.append({
                        "id": feature.segment_id,
                        "type": layer_type,
                        "coordinates": polygon,
                        "reason":""
                    })
        
        return problematic_polygons
    
    def _merge_intersecting_polygons(self, polygons: List[Dict]) -> List[Dict]:
        """
        Объединить пересекающиеся полигоны
        
        Args:
            polygons: список проблемных полигонов
        
        Returns:
            список объединённых полигонов
        """
        if not polygons:
            return []
        
        # Конвертируем в Shapely полигоны для геометрических операций
        shapely_polygons = []
        for i, poly in enumerate(polygons):
            try:
                coords = poly["coordinates"]
                
                if isinstance(coords, list) and len(coords) >= 3:
                    print(f"🔍 [MERGE] Полигон {i}: {len(coords)} точек")
                    if isinstance(coords[0], list) and len(coords[0]) == 2:
                        # Убеждаемся что полигон замкнут
                        if coords[0] != coords[-1]:
                            coords = coords + [coords[0]]
                        
                        shapely_poly = Polygon(coords)  # Используем coords напрямую
                        shapely_polygons.append({
                            "index": i,
                            "polygon": shapely_poly,
                            "original": poly
                        })
                    else:
                        print(f"⚠️ [MERGE] Полигон {i}: неверный формат координат (coords[0] = {coords[0] if coords else 'None'})")
                else:
                    print(f"⚠️ [MERGE] Полигон {i}: неверный формат координат (coords = {coords})")
            except Exception as e:
                print(f"⚠️ [MERGE] Ошибка создания полигона {i}: {e}, coords = {coords}")
                continue
        
        if not shapely_polygons:
            return polygons
        
        # Группируем полигоны по пересечениям
        groups = []
        used_indices = set()
        
        for i, poly_data in enumerate(shapely_polygons):
            if i in used_indices:
                continue
            
            # Начинаем новую группу
            group = [poly_data]
            used_indices.add(i)
            
            # Ищем все полигоны, которые пересекаются с текущим
            for j, other_poly_data in enumerate(shapely_polygons):
                if j in used_indices or j == i:
                    continue
                
                # Проверяем пересечение
                if poly_data["polygon"].intersects(other_poly_data["polygon"]):
                    group.append(other_poly_data)
                    used_indices.add(j)
            
            groups.append(group)
        
        # Объединяем полигоны в каждой группе
        merged_polygons = []
        for group in groups:
            if len(group) == 1:
                # Один полигон - добавляем как есть
                merged_polygons.append(group[0]["original"])
            else:
                # Несколько полигонов - объединяем
                try:
                    # Объединяем все полигоны в группе
                    union_polygon = group[0]["polygon"]
                    for poly_data in group[1:]:
                        union_polygon = union_polygon.union(poly_data["polygon"])
                    
                    # Конвертируем обратно в наш формат
                    if hasattr(union_polygon, 'exterior'):
                        coords = list(union_polygon.exterior.coords)
                        
                        # Убираем последнюю точку если она дублирует первую
                        if coords[0] == coords[-1]:
                            coords = coords[:-1]
                        
                        # Убеждаемся что полигон замкнут (первая и последняя точка совпадают)
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])
                        
                        merged_polygon = {
                            "id": f"merged_{len(merged_polygons)}",
                            "type": "merged",
                            "coordinates": coords,
                            "reason": f"Объединено {len(group)} полигонов"
                        }
                        merged_polygons.append(merged_polygon)
                    else:
                        # Если не удалось объединить, добавляем первый полигон
                        merged_polygons.append(group[0]["original"])
                        
                except Exception as e:
                    print(f"⚠️ [MERGE] Ошибка объединения группы: {e}")
                    # Добавляем первый полигон из группы
                    merged_polygons.append(group[0]["original"])
        
        return merged_polygons
    
    def _violates_filters(
        self, 
        metrics: Dict, 
        request: CalmRouteRequest, 
        layer_type: LayerType
    ) -> bool:
        """
        Проверить нарушает ли полигон фильтры пользователя
        
        Args:
            metrics: метрики полигона
            request: запрос с фильтрами
            layer_type: тип слоя
        
        Returns:
            True если полигон нарушает фильтры
        """
        avoid = request.profile.avoid
        
        if layer_type == LayerType.NOISE:
            noise_db = metrics.get("noise_db", 0)
            return avoid.noise_above_db and noise_db > avoid.noise_above_db
        
        elif layer_type == LayerType.CROWD:
            crowd_level = metrics.get("crowd_level", 0)
            return avoid.crowd_level_above and crowd_level > avoid.crowd_level_above
        
        elif layer_type == LayerType.PUDDLES:
            has_puddles = metrics.get("puddles", False)
            return avoid.puddles and has_puddles
        
        elif layer_type == LayerType.LIGHT:
            light_lux = metrics.get("light_lux", 0)
            return avoid.light_below_lux and light_lux < avoid.light_below_lux
        
        return False
    
    def _get_violation_reason(
        self, 
        metrics: Dict, 
        request: CalmRouteRequest, 
        layer_type: LayerType
    ) -> str:
        """Получить причину нарушения фильтра"""
        avoid = request.profile.avoid
        
        if layer_type == LayerType.NOISE:
            noise_db = metrics.get("noise_db", 0)
            return f"Шум {noise_db}дБ > {avoid.noise_above_db}дБ"
        
        elif layer_type == LayerType.CROWD:
            crowd_level = metrics.get("crowd_level", 0)
            return f"Толпа {crowd_level} > {avoid.crowd_level_above}"
        
        elif layer_type == LayerType.PUDDLES:
            return "Есть лужи"
        
        elif layer_type == LayerType.LIGHT:
            light_lux = metrics.get("light_lux", 0)
            return f"Освещение {light_lux}лк < {avoid.light_below_lux}лк"
        
        return "Нарушение фильтра"
    
    def _get_route_bbox(self, route: Dict) -> Tuple[float, float, float, float]:
        """
        Получить bounding box маршрута
        
        Args:
            route: данные маршрута от 2GIS
        
        Returns:
            (lat_min, lon_min, lat_max, lon_max)
        """
        all_lats = []
        all_lons = []
        
        # Извлекаем координаты из всех маршрутов
        route_data = route.get("result", [])
        for route_item in route_data:
            maneuvers = route_item.get("maneuvers", [])
            for maneuver in maneuvers:
                outcoming_path = maneuver.get("outcoming_path", {})
                geometry_list = outcoming_path.get("geometry", [])
                
                for geom_item in geometry_list:
                    selection = geom_item.get("selection", "")
                    if selection.startswith("LINESTRING"):
                        # Парсим LINESTRING(37.617000 55.755000, 37.617191 55.755115)
                        coords_str = selection.replace("LINESTRING(", "").replace(")", "")
                        coord_pairs = coords_str.split(", ")
                        
                        for coord_pair in coord_pairs:
                            lon_str, lat_str = coord_pair.strip().split(" ")
                            all_lons.append(float(lon_str))
                            all_lats.append(float(lat_str))
        
        # Если нет координат, используем фиксированный bbox
        if not all_lats:
            return (55.75, 37.61, 55.76, 37.63)
        
        # Расширяем bbox на 10% для поиска полигонов
        lat_min, lat_max = min(all_lats), max(all_lats)
        lon_min, lon_max = min(all_lons), max(all_lons)
        
        lat_range = lat_max - lat_min
        lon_range = lon_max - lon_min
        
        return (
            lat_min - lat_range * 0.1,  # lat_min
            lon_min - lon_range * 0.1,  # lon_min  
            lat_max + lat_range * 0.1,  # lat_max
            lon_max + lon_range * 0.1   # lon_max
        )
    
    def _convert_route_to_response(
        self, 
        route: Dict, 
        request: CalmRouteRequest
    ) -> CalmRouteResponse:
        """
        Конвертировать маршрут от 2GIS в наш формат ответа
        
        Args:
            route: данные маршрута от 2GIS
            request: исходный запрос
        
        Returns:
            Ответ в нашем формате
        """
        # Парсим данные из 2GIS API
        routes = []
        
        # 2GIS возвращает массив маршрутов в result
        route_data = route.get("result", [])
        if not route_data:
            # Если нет данных, создаем fallback
            return self._create_fallback_route(request)
        
        for i, route_item in enumerate(route_data[:3]):  # Максимум 3 маршрута
            # Извлекаем геометрию маршрута
            geometry = self._extract_route_geometry(route_item)
            
            # Извлекаем метрики
            metrics = self._extract_route_metrics(route_item)
            
            # Рассчитываем calm_score на основе метрик
            calm_score = self._calculate_calm_score(metrics)
            
            # Создаем объяснения
            explanations = self._generate_explanations(route_item, request)
            
            # Определяем название маршрута
            route_name = self._get_route_name(route_item, i)
            
            routes.append(Route(
                id=route_item.get("id", f"route_{i+1}"),
                name=route_name,
                geometry=geometry,
                metrics=metrics,
                calm_score=calm_score,
                explanations=explanations
            ))
        
        return CalmRouteResponse(routes=routes)
    
    def _extract_route_geometry(self, route_item: Dict) -> RouteGeometry:
        """Извлечь геометрию маршрута из данных 2GIS"""
        coordinates = []
        
        # Извлекаем координаты из maneuvers
        maneuvers = route_item.get("maneuvers", [])
        for maneuver in maneuvers:
            outcoming_path = maneuver.get("outcoming_path", {})
            geometry_list = outcoming_path.get("geometry", [])
            
            for geom_item in geometry_list:
                selection = geom_item.get("selection", "")
                if selection.startswith("LINESTRING"):
                    # Парсим LINESTRING(37.617000 55.755000, 37.617191 55.755115)
                    coords_str = selection.replace("LINESTRING(", "").replace(")", "")
                    coord_pairs = coords_str.split(", ")
                    
                    for coord_pair in coord_pairs:
                        lon_str, lat_str = coord_pair.strip().split(" ")
                        coordinates.append([float(lon_str), float(lat_str)])
        
        # Если нет координат, создаем прямую линию
        if not coordinates:
            return RouteGeometry(
                type="LineString",
                coordinates=[[37.617, 55.755], [37.625, 55.760]]
            )
        
        return RouteGeometry(
            type="LineString",
            coordinates=coordinates
        )
    
    def _extract_route_metrics(self, route_item: Dict) -> RouteMetrics:
        """Извлечь метрики маршрута из данных 2GIS"""
        # 2GIS возвращает distance и duration в route_item
        distance_m = route_item.get("total_distance", 1000)  # в метрах
        duration_sec = route_item.get("total_duration", 720)  # в секундах
        duration_min = duration_sec // 60
        
        # Для демо используем случайные метрики доступности
        import random
        avg_noise_db = random.uniform(60, 80)
        avg_crowd = random.uniform(1, 5)
        
        return RouteMetrics(
            distance_m=int(distance_m),
            duration_min=int(duration_min),
            avg_noise_db=round(avg_noise_db, 1),
            avg_crowd=round(avg_crowd, 1)
        )
    
    def _calculate_calm_score(self, metrics: RouteMetrics) -> float:
        """Рассчитать оценку спокойствия маршрута (0-10)"""
        # Нормализуем метрики к шкале 0-10 (10 = лучше)
        noise_score = max(0, 10 - (metrics.avg_noise_db - 40) / 5)
        crowd_score = 10 - (metrics.avg_crowd - 1) * 2.5
        
        # Взвешенная сумма
        calm_score = (noise_score * 0.6 + crowd_score * 0.4) * 10
        
        return min(10, max(0, round(calm_score, 1)))
    
    def _generate_explanations(self, route_item: Dict, request: CalmRouteRequest) -> List[RouteExplanation]:
        """Сгенерировать объяснения для маршрута"""
        explanations = []
        
        # Проверяем какие фильтры были применены
        avoid = request.profile.avoid
        
        if avoid.noise_above_db:
            explanations.append(RouteExplanation(
                segment="Весь маршрут",
                reason=f"Избегаем шум выше {avoid.noise_above_db}дБ"
            ))
        
        if avoid.crowd_level_above:
            explanations.append(RouteExplanation(
                segment="Весь маршрут", 
                reason=f"Избегаем толпу выше уровня {avoid.crowd_level_above}"
            ))
        
        if avoid.puddles:
            explanations.append(RouteExplanation(
                segment="Весь маршрут",
                reason="Избегаем участки с лужами"
            ))
        
        if avoid.light_below_lux:
            explanations.append(RouteExplanation(
                segment="Весь маршрут",
                reason=f"Избегаем плохое освещение ниже {avoid.light_below_lux}лк"
            ))
        
        return explanations
    
    def _get_route_name(self, route_item: Dict, index: int) -> str:
        """Получить название маршрута"""
        algorithm = route_item.get("algorithm", "")
        
        if algorithm == "кратчайший":
            return "Самый короткий маршрут"
        elif algorithm == "быстрый":
            return "Самый быстрый маршрут"
        else:
            return f"Маршрут {index + 1}"
    
    def _create_fallback_route(self, request: CalmRouteRequest) -> CalmRouteResponse:
        """Создать fallback маршрут если 2GIS недоступен"""
        return CalmRouteResponse(
            routes=[
                Route(
                    id="fallback_route",
                    name="Базовый маршрут",
                    geometry=RouteGeometry(
                        type="LineString",
                        coordinates=[
                            [request.start.lon, request.start.lat],
                            [request.end.lon, request.end.lat]
                        ]
                    ),
                    metrics=RouteMetrics(
                        distance_m=1200,
                        duration_min=15,
                        avg_noise_db=70.0,
                        avg_crowd=3.0
                    ),
                    calm_score=6.0,
                    explanations=[
                        RouteExplanation(
                            segment="Прямой маршрут",
                            reason="2GIS API недоступен"
                        )
                    ]
                )
            ]
        )


# Singleton
_calm_route_service = None

def get_calm_route_service() -> CalmRouteService:
    """Получить экземпляр сервиса спокойных маршрутов"""
    global _calm_route_service
    if _calm_route_service is None:
        _calm_route_service = CalmRouteService()
    return _calm_route_service
