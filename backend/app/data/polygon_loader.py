import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from app.const import USE_REAL_DATA


class PolygonLoader:
    
    def __init__(self, gis_service=None):
        self.gis_service = gis_service
        self.layer_files = {
            "noise": "app/data/polygons_noise.json",
            "light": "app/data/polygons_light.json",
            "crowd": "app/data/polygons_crowd.json",
            "puddles": "app/data/polygons_puddles.json"
        }
        
        self.polygons_by_layer = {}
        for layer_type, file_path in self.layer_files.items():
            if layer_type == "light" and self.gis_service:
                print(f"✅ [LIGHT] Будет использоваться 2GIS API для поиска ТЦ")
                self.polygons_by_layer[layer_type] = []
            else:
                self.polygons_by_layer[layer_type] = self._load_data(file_path, layer_type)
    
    def _load_data(self, file_path: str, layer_type: str) -> List[Dict]:
        data_file = Path(file_path)
        
        if not data_file.exists():
            print(f"⚠️ [{layer_type.upper()}] Файл не найден: {file_path}")
            return []
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                polygons = data.get("polygons", [])
            print(f"✅ [{layer_type.upper()}] Загружено {len(polygons)} полигонов из {file_path}")
            return polygons
        except json.JSONDecodeError as e:
            print(f"❌ [{layer_type.upper()}] Ошибка парсинга JSON: {e}")
            return []
        except Exception as e:
            print(f"❌ [{layer_type.upper()}] Ошибка при загрузке: {e}")
            return []
    
    def has_data_for_layer(self, layer_type: str) -> bool:
        return (
            layer_type in self.polygons_by_layer and 
            len(self.polygons_by_layer[layer_type]) > 0
        )
    
    async def find_polygons_in_bbox_async(
        self, 
        layer_type: str,
        bbox: Tuple[float, float, float, float]
    ) -> List[Dict]:
        if layer_type == "light" and self.gis_service and USE_REAL_DATA:
            try:
                print(f"✅ [LIGHT] Используем асинхронный метод (2GIS API)")
                gis_polygons = await self.gis_service.get_light_polygons(bbox)
                print(f"✅ [LIGHT] Результат запроса: {gis_polygons}")
                if gis_polygons:
                    return gis_polygons
            except Exception as e:
                print(f"⚠️ [LIGHT] Ошибка загрузки из 2GIS, используем fallback: {e}")
        print(f"✅ [LIGHT] Используем файлы")
        return self.find_polygons_in_bbox(layer_type, bbox)
    
    def find_polygons_in_bbox(
        self, 
        layer_type: str,
        bbox: Tuple[float, float, float, float]
    ) -> List[Dict]:
        if layer_type not in self.polygons_by_layer:
            return []
        
        polygons_data = self.polygons_by_layer[layer_type]
        result = []
        
        for polygon in polygons_data:
            if self._intersects_bbox(polygon["coordinates"], bbox):
                result.append(polygon)
        
        return result
    
    def _intersects_bbox(
        self, 
        coords: List[List[float]], 
        bbox: Tuple[float, float, float, float]
    ) -> bool:
        lat_min, lon_min, lat_max, lon_max = bbox
        
        poly_lons = [coord[0] for coord in coords]
        poly_lats = [coord[1] for coord in coords]
        
        poly_lon_min = min(poly_lons)
        poly_lon_max = max(poly_lons)
        poly_lat_min = min(poly_lats)
        poly_lat_max = max(poly_lats)
        
        return not (
            poly_lon_max < lon_min or
            poly_lon_min > lon_max or
            poly_lat_max < lat_min or
            poly_lat_min > lat_max
        )
    
    def convert_to_segments(self, polygons: List[Dict]) -> List[Dict]:
        segments = []
        
        for i, poly in enumerate(polygons):
            coords = poly["coordinates"]
            if coords[0] != coords[-1]:
                coords = coords + [coords[0]]
            
            segment = {
                "id": poly.get("id", f"polygon_{i:03d}"),
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords]
                },
                "street_name": poly.get("street_name", ""),
                "metrics": poly.get("metrics", {}),
                "confidence": poly.get("confidence", 0.9),
                "last_updated": poly.get("last_updated")
            }
            segments.append(segment)
        
        return segments


_polygon_loader: Optional[PolygonLoader] = None

def get_polygon_loader(gis_service=None) -> PolygonLoader:
    global _polygon_loader
    if _polygon_loader is None:
        _polygon_loader = PolygonLoader(gis_service=gis_service)
    elif gis_service is not None and _polygon_loader.gis_service is None:
        print(f"🔄 Обновляем gis_service в PolygonLoader")
        _polygon_loader.gis_service = gis_service
    return _polygon_loader
