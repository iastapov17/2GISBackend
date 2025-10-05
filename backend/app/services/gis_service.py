import httpx
import math
from typing import List, Dict, Tuple, Optional


class GisService:
    
    def __init__(self, api_key: Optional[str] = '49186240-cdc8-4f73-b64f-7933d62178ae'):
        self.api_key = api_key
        self.places_url = "https://catalog.api.2gis.com/3.0"
        self.routing_url = "https://routing.api.2gis.com/routing/7.0.0/global"
        self.timeout = 10.0
    
    async def search_places(
        self,
        query: str,
        bbox: Tuple[float, float, float, float],
        limit: int = 20
    ) -> List[Dict]:
        lat_min, lon_min, lat_max, lon_max = bbox
        
        params = {
            "q": query,
            "viewpoint1": f"{lon_min},{lat_max}",
            "viewpoint2": f"{lon_max},{lat_min}",
            "type": "branch",
            "fields": "items.id,items.name,items.point,items.rubrics,items.address_name,items.address_comment",
            "page_size": limit
        }
        
        if self.api_key:
            params["key"] = self.api_key
        
        print(f"✅ [2GIS] Поиск мест: {query} в {bbox}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.places_url}/items",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("result", {}).get("items", [])
                    
                    print(f"✅ [2GIS] Найдено {len(items)} мест")
                    
                    places = []
                    for item in items:
                        point = item.get("point")
                        if point:
                            place = {
                                "id": item.get("id"),
                                "name": item.get("name", ""),
                                "latitude": point.get("lat"),
                                "longitude": point.get("lon"),
                                "address": item.get("address_name", ""),
                                "rubrics": item.get("rubrics", []),
                                "address_comment": item.get("address_comment", "")
                            }
                            places.append(place)
                    
                    return places
                else:
                    print(f"⚠️ [2GIS] Ошибка API: {response.status_code}")
                    return []
        
        except httpx.TimeoutException:
            print(f"⚠️ [2GIS] Timeout при запросе к API")
            return []
        except Exception as e:
            print(f"⚠️ [2GIS] Ошибка при запросе: {e}")
            return []

    async def get_shopping_centers(
        self, 
        bbox: Tuple[float, float, float, float],
        limit: int = 50
    ) -> List[Dict]:
        lat_min, lon_min, lat_max, lon_max = bbox
        params = {
            "q": "торговый центр",
            "viewpoint1": f"{lon_min},{lat_max}",
            "viewpoint2": f"{lon_max},{lat_min}",
            "type": "branch",
            "fields": "items.point",
            "page_size": limit
        }
        
        if self.api_key:
            print(f"✅ [2GIS] Используем API ключ: {self.api_key}")
            params["key"] = self.api_key
        
        print(f"✅ [2GIS] Запрос к API: {params}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.places_url}/items",
                    params=params
                )

                print(f"✅ [2GIS] Результат запроса: {response.json()}")
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("result", {}).get("items", [])
                    
                    print(f"✅ [2GIS] Найдено {len(items)} торговых центров")
                    
                    points = []
                    for item in items:
                        point = item.get("point")
                        if point:
                            points.append({
                                "id": item.get("id"),
                                "name": item.get("name", "ТЦ"),
                                "lat": point.get("lat"),
                                "lon": point.get("lon")
                            })
                    
                    return points
                else:
                    print(f"⚠️ [2GIS] Ошибка API: {response.status_code}")
                    return []
        
        except httpx.TimeoutException:
            print(f"⚠️ [2GIS] Timeout при запросе к API")
            return []
        except Exception as e:
            print(f"⚠️ [2GIS] Ошибка при запросе: {e}")
            return []
    
    def create_polygon_around_point(
        self, 
        lat: float, 
        lon: float, 
        radius_m: int = 100,
        num_points: int = 4
    ) -> List[List[float]]:
        lat_km_per_deg = 111.0
        lon_km_per_deg = 111.0 * math.cos(math.radians(lat))
        
        radius_lat = (radius_m / 1000.0) / lat_km_per_deg
        radius_lon = (radius_m / 1000.0) / lon_km_per_deg
        
        coordinates = []
        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            point_lat = lat + radius_lat * math.sin(angle)
            point_lon = lon + radius_lon * math.cos(angle)
            coordinates.append([point_lon, point_lat])
        
        coordinates.append(coordinates[0])
        
        return coordinates
    
    async def get_light_polygons(
        self, 
        bbox: Tuple[float, float, float, float]
    ) -> List[Dict]:
        print(f"✅ [2GIS] Запрос к API: {bbox}")
        shopping_centers = await self.get_shopping_centers(bbox)
        
        if not shopping_centers:
            return []
        
        polygons = []
        for sc in shopping_centers:
            polygon_coords = self.create_polygon_around_point(
                lat=sc["lat"],
                lon=sc["lon"],
                radius_m=100,
                num_points=16
            )
            
            polygons.append({
                "id": f"light_tc_{sc['id']}",
                "coordinates": polygon_coords,
                "street_name": sc["name"],
                "metrics": {
                    "noise_db": 65.0,
                    "crowd_level": 4,
                    "light_lux": 180.0,
                    "puddles": False
                }
            })
        
        print(f"✅ [2GIS] Создано {len(polygons)} полигонов освещённости из ТЦ")
        return polygons
    
    async def get_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        profile: str = "pedestrian",
        exclude_polygons: List[Dict] = None
    ) -> Dict:
        start_lat, start_lon = start
        end_lat, end_lon = end
        
        payload = {
            "points": [
                {"lat": start_lat, "lon": start_lon},
                {"lat": end_lat, "lon": end_lon}
            ],
            "locale": "ru",
            "transport": profile,
            "output": "detailed"
        }
        
        if exclude_polygons:
            payload["exclude"] = exclude_polygons
        
        params = {}
        if self.api_key:
            params["key"] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.routing_url}",
                    json=payload,
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ [2GIS ROUTING] Маршрут построен успешно")
                    return data
                else:
                    print(f"⚠️ [2GIS ROUTING] Ошибка API: {response.status_code} {response.json()}")
                    return {}
        
        except httpx.TimeoutException:
            print(f"⚠️ [2GIS ROUTING] Timeout при запросе к API")
            return {}
        except Exception as e:
            print(f"⚠️ [2GIS ROUTING] Ошибка при запросе: {e}")
            return {}
    
    def create_exclude_polygon(self, polygon_coords: List[List[float]]) -> Dict:
        return {
            "severity": "hard",
            "type": "polyline",
            "points": [{"lon": lon, "lat": lat} for lon, lat in polygon_coords],
        }


_gis_service = None

def get_gis_service(api_key: Optional[str] = None) -> GisService:
    global _gis_service
    if _gis_service is None:
        _gis_service = GisService(api_key=api_key)
    return _gis_service

