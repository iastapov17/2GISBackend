import random
from typing import Dict, List, Any, Tuple
from app.schemas.places import AccessibilityFilter


class AccessibilityGenerator:
    
    def __init__(self):
        self.rubric_probabilities = {
            "restaurant": {
                "wheelchair_access": 0.6,
                "accessible_parking": 0.4,
                "accessible_toilet": 0.7,
                "service_dog_friendly": 0.8,
                "low_noise": 0.3,
                "low_light": 0.5,
                "low_crowd": 0.2,
                "braille_or_audio": 0.1,
                "hearing_loop": 0.1
            },
            "museum": {
                "wheelchair_access": 0.9,
                "accessible_parking": 0.7,
                "accessible_toilet": 0.8,
                "service_dog_friendly": 0.9,
                "low_noise": 0.8,
                "low_light": 0.6,
                "low_crowd": 0.4,
                "braille_or_audio": 0.8,
                "hearing_loop": 0.7
            },
            "park": {
                "wheelchair_access": 0.7,
                "accessible_parking": 0.6,
                "accessible_toilet": 0.5,
                "service_dog_friendly": 0.9,
                "low_noise": 0.9,
                "low_light": 0.8,
                "low_crowd": 0.6,
                "braille_or_audio": 0.3,
                "hearing_loop": 0.2
            },
            "library": {
                "wheelchair_access": 0.8,
                "accessible_parking": 0.6,
                "accessible_toilet": 0.7,
                "service_dog_friendly": 0.7,
                "low_noise": 0.95,
                "low_light": 0.7,
                "low_crowd": 0.8,
                "braille_or_audio": 0.9,
                "hearing_loop": 0.8
            },
            "shopping_center": {
                "wheelchair_access": 0.8,
                "accessible_parking": 0.9,
                "accessible_toilet": 0.8,
                "service_dog_friendly": 0.6,
                "low_noise": 0.1,
                "low_light": 0.9,
                "low_crowd": 0.1,
                "braille_or_audio": 0.3,
                "hearing_loop": 0.2
            },
            "medical": {
                "wheelchair_access": 0.95,
                "accessible_parking": 0.9,
                "accessible_toilet": 0.95,
                "service_dog_friendly": 0.9,
                "low_noise": 0.7,
                "low_light": 0.8,
                "low_crowd": 0.5,
                "braille_or_audio": 0.6,
                "hearing_loop": 0.8
            },
            "bank": {
                "wheelchair_access": 0.7,
                "accessible_parking": 0.6,
                "accessible_toilet": 0.6,
                "service_dog_friendly": 0.5,
                "low_noise": 0.8,
                "low_light": 0.9,
                "low_crowd": 0.6,
                "braille_or_audio": 0.4,
                "hearing_loop": 0.6
            }
        }
        
        self.default_probabilities = {
            "wheelchair_access": 0.5,
            "accessible_parking": 0.4,
            "accessible_toilet": 0.6,
            "service_dog_friendly": 0.6,
            "low_noise": 0.5,
            "low_light": 0.6,
            "low_crowd": 0.4,
            "braille_or_audio": 0.3,
            "hearing_loop": 0.3
        }
    
    def generate_accessibility_data(self, place_data: Dict[str, Any]) -> Dict[str, Any]:
        rubrics = place_data.get("rubrics", [])
        place_type = self._determine_place_type(rubrics)
        
        probabilities = self.rubric_probabilities.get(place_type, self.default_probabilities)
        
        accessibility_conditions = []
        
        for filter_type in AccessibilityFilter:
            filter_key = filter_type.value
            probability = probabilities.get(filter_key, 0.5)
            
            is_available = random.random() < probability
            
            if is_available:
                rating = random.uniform(3.0, 5.0)
                
                condition = {
                    "filter_type": filter_key,
                    "name": self._get_condition_name(filter_key),
                    "rating": round(rating, 1)
                }
                accessibility_conditions.append(condition)
        
        all_ratings = {}
        for condition in accessibility_conditions:
            filter_type = condition["filter_type"]
            rating = condition["rating"]
            all_ratings[filter_type] = [rating]
        
        return {
            "accessibility_conditions": accessibility_conditions,
            "all_ratings": all_ratings,
            "overall_rating": self._calculate_overall_rating(accessibility_conditions)
        }
    
    def _determine_place_type(self, rubrics: List[Any]) -> str:
        if not rubrics:
            return "unknown"
        
        first_rubric = rubrics[0]
        
        if isinstance(first_rubric, dict):
            rubric_name = first_rubric.get("name", "").lower()
        elif isinstance(first_rubric, str):
            rubric_name = first_rubric.lower()
        else:
            rubric_name = str(first_rubric).lower()
        if any(word in rubric_name for word in ["ресторан", "кафе", "бар", "столовая"]):
            return "restaurant"
        elif any(word in rubric_name for word in ["музей", "галерея", "выставка"]):
            return "museum"
        elif any(word in rubric_name for word in ["парк", "сквер", "сад"]):
            return "park"
        elif any(word in rubric_name for word in ["библиотека", "читальня"]):
            return "library"
        elif any(word in rubric_name for word in ["торговый центр", "молл", "пассаж"]):
            return "shopping_center"
        elif any(word in rubric_name for word in ["больница", "поликлиника", "медицинский"]):
            return "medical"
        elif any(word in rubric_name for word in ["банк", "кредит"]):
            return "bank"
        else:
            return "unknown"
    
    def _get_condition_name(self, filter_key: str) -> str:
        names = {
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
        return names.get(filter_key, filter_key)
    
    def _calculate_overall_rating(self, conditions: List[Dict[str, Any]]) -> float:
        if not conditions:
            return 0.0
        
        ratings = [cond["rating"] for cond in conditions]
        return round(sum(ratings) / len(ratings), 1)


_generator = None

def get_accessibility_generator() -> AccessibilityGenerator:
    global _generator
    if _generator is None:
        _generator = AccessibilityGenerator()
    return _generator
