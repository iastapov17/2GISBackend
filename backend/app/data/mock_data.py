import random
from typing import List, Tuple, Dict, Any
from datetime import datetime, timedelta


class MockDataGenerator:
    
    def __init__(self, use_real_data: bool = True, gis_service=None):
        self.center = (55.7558, 37.6173)
        
        self.use_real_data = use_real_data
        self.polygon_loader = None
        
        if use_real_data:
            try:
                from app.data.polygon_loader import get_polygon_loader
                self.polygon_loader = get_polygon_loader(gis_service=gis_service)
            except Exception as e:
                print(f"⚠️ Не удалось загрузить polygon_loader: {e}")
        
        self.street_types = [
            "проспект",
            "улица",
            "переулок",
            "бульвар"
        ]
        self.street_names = [
            "Тверская",
            "Арбат",
            "Маросейка",
            "Покровка",
            "Мясницкая",
            "Никольская",
            "Петровка",
            "Кузнецкий мост",
            "Сретенка",
            "Лубянка"
        ]
    
    async def generate_segments_in_bbox_async(
        self, 
        bbox: Tuple[float, float, float, float],
        layer_type: str = "noise",
        count: int = 30
    ) -> List[dict]:
        """
        Сгенерировать сегменты улиц в заданной области (асинхронно)
        
        Для света - использует 2GIS API если доступен
        Для других - загружает из файлов или генерирует синтетику
        
        Args:
            bbox: (lat_min, lon_min, lat_max, lon_max)
            layer_type: тип слоя (noise, light, crowd, puddles)
            count: количество сегментов (для синтетики)
        
        Returns:
            Список сегментов с геометрией и метриками
        """
        # Попробовать загрузить реальные данные для конкретного типа слоя
        if self.use_real_data and self.polygon_loader:
            # Для света используем асинхронный метод (2GIS API)
            if layer_type == "light":
                print(f"✅ [{layer_type.upper()}] Используем асинхронный метод (2GIS API)")
                real_polygons = await self.polygon_loader.find_polygons_in_bbox_async(layer_type, bbox)
                if real_polygons:
                    print(f"✅ [{layer_type.upper()}] Используем {len(real_polygons)} реальных полигонов")
                    return self.polygon_loader.convert_to_segments(real_polygons)[:200]
            # Для остальных - синхронный
            elif self.polygon_loader.has_data_for_layer(layer_type):
                real_polygons = self.polygon_loader.find_polygons_in_bbox(layer_type, bbox)
                if real_polygons:
                    print(f"✅ [{layer_type.upper()}] Используем {len(real_polygons)} реальных полигонов")
                    return self.polygon_loader.convert_to_segments(real_polygons)[:200]
        
        # Иначе генерируем синтетику
        print(f"⚙️ [{layer_type.upper()}] Генерируем {count} синтетических полигонов")
        # return self._generate_synthetic_segments(bbox, count)
        return []
    
    def generate_segments_in_bbox(
        self, 
        bbox: Tuple[float, float, float, float],
        layer_type: str = "noise",
        count: int = 30
    ) -> List[dict]:
        """
        Сгенерировать сегменты улиц в заданной области (синхронно)
        
        Если доступны реальные данные для layer_type - использует их,
        иначе генерирует синтетические.
        
        Args:
            bbox: (lat_min, lon_min, lat_max, lon_max)
            layer_type: тип слоя (noise, light, crowd, puddles)
            count: количество сегментов (для синтетики)
        
        Returns:
            Список сегментов с геометрией и метриками
        """
        # Попробовать загрузить реальные данные для конкретного типа слоя
        if self.use_real_data and self.polygon_loader:
            if self.polygon_loader.has_data_for_layer(layer_type):
                real_polygons = self.polygon_loader.find_polygons_in_bbox(layer_type, bbox)
                if real_polygons:
                    print(f"✅ [{layer_type.upper()}] Используем {len(real_polygons)} реальных полигонов")
                    return self.polygon_loader.convert_to_segments(real_polygons)[:200]
        
        # Иначе генерируем синтетику
        print(f"⚙️ [{layer_type.upper()}] Генерируем {count} синтетических полигонов")
        # return self._generate_synthetic_segments(bbox, count)
        return []
    
    def _generate_synthetic_segments(
        self,
        bbox: Tuple[float, float, float, float],
        count: int = 30
    ) -> List[dict]:
        """Генерация синтетических сегментов"""
        lat_min, lon_min, lat_max, lon_max = bbox
        segments = []
        
        for i in range(count):
            # Случайная точка в bbox
            center_lat = random.uniform(lat_min, lat_max)
            center_lon = random.uniform(lon_min, lon_max)
            
            # Создаём полигон (квадрат ~100-150м)
            size = random.uniform(0.0008, 0.0012)  # ~100-150м
            
            # Координаты полигона (замкнутый квадрат)
            polygon_coords = [
                [center_lon - size, center_lat - size],  # bottom-left
                [center_lon + size, center_lat - size],  # bottom-right
                [center_lon + size, center_lat + size],  # top-right
                [center_lon - size, center_lat + size],  # top-left
                [center_lon - size, center_lat - size]   # замыкаем полигон
            ]
            
            # Определяем тип улицы по расстоянию от центра
            dist_from_center = self._distance_to_center(center_lat, center_lon)
            
            segment = {
                "id": f"segment_{i:03d}",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [polygon_coords]  # Polygon требует массив массивов
                },
                "street_name": f"{random.choice(self.street_types)} {random.choice(self.street_names)}",
                "metrics": self._generate_metrics_for_location(
                    center_lat, 
                    center_lon, 
                    dist_from_center
                ),
                "confidence": random.uniform(0.7, 0.95),
                "last_updated": datetime.utcnow() - timedelta(minutes=random.randint(5, 120))
            }
            segments.append(segment)
        
        return segments
    
    def _generate_metrics_for_location(
        self, 
        lat: float, 
        lon: float,
        dist_from_center: float
    ) -> dict:
        """
        Сгенерировать метрики для локации
        
        Эвристики:
        - Чем ближе к центру → шумнее и люднее
        - Проспекты → шумные (70-85 дБ)
        - Переулки → тихие (50-65 дБ)
        - Снег: 80% расчищено
        """
        # Базовый шум зависит от расстояния до центра
        # Центр: 70-85 дБ, окраины: 50-65 дБ
        if dist_from_center < 1.0:  # < 1 км
            noise_db = random.uniform(70, 85)
            crowd_level = random.randint(3, 5)
        elif dist_from_center < 2.0:  # 1-2 км
            noise_db = random.uniform(60, 75)
            crowd_level = random.randint(2, 4)
        else:  # > 2 км
            noise_db = random.uniform(50, 65)
            crowd_level = random.randint(1, 3)
        
        return {
            "noise_db": round(noise_db, 1),
            "crowd_level": crowd_level,
            "light_lux": random.randint(50, 200),
            "puddles": random.random() > 0.7  # 30% лужи
        }
    
    def _distance_to_center(self, lat: float, lon: float) -> float:
        """
        Примерное расстояние до центра (в км)
        Упрощённая формула без учёта сферичности Земли
        """
        dlat = lat - self.center[0]
        dlon = lon - self.center[1]
        # 1 градус ≈ 111 км
        return ((dlat ** 2 + dlon ** 2) ** 0.5) * 111
    
    def generate_mock_routes(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        count: int = 3
    ) -> List[dict]:
        """
        Сгенерировать несколько мок-маршрутов между точками
        
        Args:
            start: (lat, lon) начальная точка
            end: (lat, lon) конечная точка
            count: количество вариантов
        
        Returns:
            Список маршрутов с геометрией и метриками
        """
        routes = []
        
        for i in range(count):
            # Генерируем путь с небольшими отклонениями
            path = self._generate_path(start, end, variation=i * 0.0005)
            
            # Генерируем сегменты вдоль пути
            segments = self._generate_segments_along_path(path)
            
            # Считаем общее расстояние и время
            distance_m = self._calculate_distance(path)
            duration_min = int(distance_m / 80)  # ~5 км/ч = 80 м/мин
            
            route = {
                "geometry": {
                    "type": "LineString",
                    "coordinates": path
                },
                "segments": segments,
                "distance_m": distance_m,
                "duration_min": max(5, duration_min)
            }
            routes.append(route)
        
        return routes
    
    def _generate_path(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        variation: float = 0.0
    ) -> List[List[float]]:
        """
        Сгенерировать путь между двумя точками
        
        Args:
            start: начальная точка
            end: конечная точка
            variation: величина отклонения от прямой
        
        Returns:
            Список координат [[lon, lat], ...]
        """
        start_lat, start_lon = start
        end_lat, end_lon = end
        
        # Количество промежуточных точек
        steps = random.randint(5, 10)
        
        path = [[start_lon, start_lat]]
        
        for i in range(1, steps):
            t = i / steps
            
            # Линейная интерполяция с отклонением
            lat = start_lat + (end_lat - start_lat) * t
            lon = start_lon + (end_lon - start_lon) * t
            
            # Добавляем случайное отклонение (извилистость)
            lat += random.uniform(-variation, variation)
            lon += random.uniform(-variation, variation)
            
            path.append([lon, lat])
        
        path.append([end_lon, end_lat])
        
        return path
    
    def _generate_segments_along_path(
        self, 
        path: List[List[float]]
    ) -> List[dict]:
        """
        Сгенерировать сегменты улиц вдоль пути
        """
        segments = []
        
        for i in range(len(path) - 1):
            lon, lat = path[i]
            
            dist_from_center = self._distance_to_center(lat, lon)
            
            segment = {
                "id": f"route_segment_{i}",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [path[i], path[i + 1]]
                },
                "street_name": f"{random.choice(self.street_types)} {random.choice(self.street_names)}",
                "metrics": self._generate_metrics_for_location(
                    lat, lon, dist_from_center
                )
            }
            segments.append(segment)
        
        return segments
    
    def _calculate_distance(self, path: List[List[float]]) -> int:
        """
        Примерно вычислить длину пути в метрах
        """
        total_distance = 0
        
        for i in range(len(path) - 1):
            lon1, lat1 = path[i]
            lon2, lat2 = path[i + 1]
            
            # Упрощённая формула
            dlat = abs(lat2 - lat1) * 111000  # метры
            dlon = abs(lon2 - lon1) * 111000 * 0.6  # коррекция на широту
            
            distance = (dlat ** 2 + dlon ** 2) ** 0.5
            total_distance += distance
        
        return int(total_distance)
    
    def generate_mock_places(
        self,
        query: str,
        location: Tuple[float, float],
        filters: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Сгенерировать моковые места для поиска
        
        Args:
            query: поисковый запрос
            location: (lat, lon) локация пользователя
            filters: список фильтров доступности
        
        Returns:
            Список мест с данными о доступности
        """
        if filters is None:
            filters = []
        
        # Базовые данные мест
        places_data = [
            {
                "name": "Кафе 'Уютное место'",
                "accessibility": {
                    "wheelchair_access": (True, 4.5),
                    "accessible_parking": (True, 4.0),
                    "accessible_toilet": (True, 4.2),
                    "service_dog_friendly": (True, 4.8),
                    "low_noise": (True, 4.7),
                    "low_light": (True, 4.3),
                    "low_crowd": (True, 4.1),
                    "braille_or_audio": (False, 0.0),
                    "hearing_loop": (False, 0.0)
                }
            },
            {
                "name": "Музей современного искусства",
                "accessibility": {
                    "wheelchair_access": (True, 5.0),
                    "accessible_parking": (True, 4.8),
                    "accessible_toilet": (True, 4.9),
                    "service_dog_friendly": (True, 5.0),
                    "low_noise": (True, 4.6),
                    "low_light": (True, 4.4),
                    "low_crowd": (False, 2.1),
                    "braille_or_audio": (True, 4.7),
                    "hearing_loop": (True, 4.5)
                }
            },
            {
                "name": "Парк 'Тишина'",
                "accessibility": {
                    "wheelchair_access": (True, 4.3),
                    "accessible_parking": (True, 3.8),
                    "accessible_toilet": (True, 3.5),
                    "service_dog_friendly": (True, 4.9),
                    "low_noise": (True, 4.8),
                    "low_light": (True, 4.2),
                    "low_crowd": (True, 4.5),
                    "braille_or_audio": (False, 0.0),
                    "hearing_loop": (False, 0.0)
                }
            },
            {
                "name": "Библиотека 'Доступная книга'",
                "accessibility": {
                    "wheelchair_access": (True, 4.7),
                    "accessible_parking": (True, 4.2),
                    "accessible_toilet": (True, 4.4),
                    "service_dog_friendly": (True, 4.6),
                    "low_noise": (True, 4.9),
                    "low_light": (True, 4.1),
                    "low_crowd": (True, 4.3),
                    "braille_or_audio": (True, 5.0),
                    "hearing_loop": (True, 4.8)
                }
            },
            {
                "name": "Ресторан 'Громкая музыка'",
                "accessibility": {
                    "wheelchair_access": (True, 3.2),
                    "accessible_parking": (False, 0.0),
                    "accessible_toilet": (True, 3.8),
                    "service_dog_friendly": (False, 0.0),
                    "low_noise": (False, 1.2),
                    "low_light": (False, 2.1),
                    "low_crowd": (False, 1.8),
                    "braille_or_audio": (False, 0.0),
                    "hearing_loop": (False, 0.0)
                }
            }
        ]
        
        # Генерируем места
        places = []
        lat, lon = location
        
        for i, place_data in enumerate(places_data):
            # Случайная точка рядом с пользователем
            lat_offset = random.uniform(-0.01, 0.01)  # ~1км
            lon_offset = random.uniform(-0.01, 0.01)
            
            place_lat = lat + lat_offset
            place_lon = lon + lon_offset
            
            # Генерируем отзывы
            reviews = self._generate_reviews(place_data["name"])
            
            # Формируем условия доступности (только доступные)
            accessibility_conditions = []
            for filter_key, (available, rating) in place_data["accessibility"].items():
                if available and rating > 0:
                    condition = self._create_accessibility_condition(filter_key, available, rating)
                    accessibility_conditions.append(condition)
            
            # Вычисляем общий рейтинг
            available_ratings = [rating for _, rating in place_data["accessibility"].items() if rating > 0]
            overall_rating = sum(available_ratings) / len(available_ratings) if available_ratings else 0
            
            place = {
                "id": f"place_{i:03d}",
                "name": place_data["name"],
                "location": {
                    "latitude": place_lat,
                    "longitude": place_lon
                },
                "accessibility_conditions": accessibility_conditions,
                "reviews": reviews,
                "overall_rating": round(overall_rating, 1)
            }
            
            # Фильтруем по запрошенным фильтрам
            if filters:
                has_required_filters = all(
                    any(cond["filter_type"] == f for cond in accessibility_conditions)
                    for f in filters
                )
                if has_required_filters:
                    places.append(place)
            else:
                places.append(place)
        
        return places
    
    def _create_accessibility_condition(self, filter_key: str, available: bool, rating: float) -> Dict[str, Any]:
        """Создать условие доступности"""
        filter_info = {
            "wheelchair_access": "Пандус или лифт",
            "accessible_parking": "Парковка для инвалидов",
            "accessible_toilet": "Доступный туалет",
            "service_dog_friendly": "С собакой-поводырём",
            "low_noise": "Низкий уровень шума",
            "low_light": "Мягкое освещение",
            "low_crowd": "Небольшая толпа",
            "braille_or_audio": "Шрифт Брайля / аудиоподсказки",
            "hearing_loop": "Поддержка слуховых аппаратов"
        }
        
        name = filter_info.get(filter_key, filter_key)
        
        return {
            "filter_type": filter_key,
            "name": name,
            "rating": rating
        }
    
    def _generate_reviews(self, place_name: str) -> List[Dict[str, Any]]:
        """Сгенерировать отзывы для места"""
        review_templates = [
            "Отличное место, очень доступно! Есть пандус и широкие проходы",
            "Хорошая атмосфера, но шумно. Нет индукционной петли",
            "Прекрасное обслуживание, рекомендую. Все условия доступности соблюдены",
            "Уютно и тихо, идеально для работы. Мягкое освещение, низкий уровень шума",
            "Дорого, но качественно. Есть аудиогиды и Брайль"
        ]
        
        reviews = []
        num_reviews = random.randint(2, 5)
        
        for i in range(num_reviews):
            review = {
                "id": f"review_{i}",
                "author": f"{random.choice(['Анна', 'Михаил', 'Елена', 'Дмитрий', 'Ольга'])} {random.choice(['С.', 'М.', 'К.', 'В.', 'П.'])}",
                "rating": random.randint(3, 5),
                "text": random.choice(review_templates),
                "date": datetime.utcnow() - timedelta(days=random.randint(1, 30))
            }
            reviews.append(review)
        
        return reviews


# Singleton для использования в сервисах
_generator = MockDataGenerator()


def get_mock_generator() -> MockDataGenerator:
    """Получить экземпляр генератора"""
    return _generator

