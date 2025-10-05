import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class PlacesStorage:
    
    def __init__(self, data_dir: str = "app/data/places"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.accessibility_file = self.data_dir / "accessibility.json"
        self.reviews_file = self.data_dir / "reviews.json"
        
        self.accessibility_data = self._load_json(self.accessibility_file)
        self.reviews_data = self._load_json(self.reviews_file)
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Ошибка загрузки {file_path}: {e}")
                return {}
        return {}
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Ошибка сохранения {file_path}: {e}")
            return False
    
    def get_place_accessibility(self, place_id: str) -> Optional[Dict[str, Any]]:
        return self.accessibility_data.get(place_id)
    
    def save_place_accessibility(self, place_id: str, accessibility_data: Dict[str, Any]) -> bool:
        """Сохранить данные о доступности места"""
        self.accessibility_data[place_id] = {
            **accessibility_data,
            "updated_at": datetime.utcnow().isoformat()
        }
        return self._save_json(self.accessibility_file, self.accessibility_data)
    
    def get_place_reviews(self, place_id: str) -> List[Dict[str, Any]]:
        """Получить отзывы о месте"""
        return self.reviews_data.get(place_id, [])
    
    def add_place_review(self, place_id: str, review: Dict[str, Any]) -> bool:
        """Добавить отзыв о месте"""
        if place_id not in self.reviews_data:
            self.reviews_data[place_id] = []
        
        review["id"] = f"review_{len(self.reviews_data[place_id]) + 1}"
        review["date"] = datetime.utcnow().isoformat()
        
        self.reviews_data[place_id].append(review)
        return self._save_json(self.reviews_file, self.reviews_data)
    
    def has_place_data(self, place_id: str) -> bool:
        """Проверить есть ли данные о месте"""
        return place_id in self.accessibility_data or place_id in self.reviews_data


_storage = None

def get_places_storage() -> PlacesStorage:
    """Получить экземпляр хранилища"""
    global _storage
    if _storage is None:
        _storage = PlacesStorage()
    return _storage
