from typing import List, Dict, Any, Tuple
from app.data.mock_data import get_mock_generator
from app.data.places_storage import get_places_storage
from app.services.gis_service import get_gis_service
from app.services.accessibility_generator import get_accessibility_generator
from app.schemas.places import (
    Place, 
    PlaceSearchRequest, 
    PlaceSearchResponse,
    PlaceLocation,
    Review,
    AddReviewRequest,
    AccessibilityRating
)


class PlacesService:
    
    def __init__(self):
        self.mock_generator = get_mock_generator()
        self.gis_service = get_gis_service()
        self.storage = get_places_storage()
        self.accessibility_generator = get_accessibility_generator()
    
    async def search_places(self, request: PlaceSearchRequest) -> PlaceSearchResponse:
        lat, lon = request.location.latitude, request.location.longitude
        bbox = self._create_bbox(lat, lon, radius_km=5.0)
        
        gis_places = await self.gis_service.search_places(
            query=request.query,
            bbox=bbox,
            limit=20
        )
        
        if not gis_places:
            print("⚠️ [PLACES] 2GIS API не вернул результатов, используем моковые данные")
            return await self._get_mock_places(request)
        
        places = []
        filter_values = [f.value for f in request.filters] if request.filters else []
        for gis_place in gis_places:
            place = await self._process_place(gis_place, filter_values)
            if place:
                places.append(place)
        
        return PlaceSearchResponse(places=places)
    
    async def _process_place(self, gis_place: Dict[str, Any], filters: List[str]) -> Place:
        place_id = gis_place["id"]
        
        accessibility_data = self.storage.get_place_accessibility(place_id)
        
        if not accessibility_data:
            print(f"✅ [PLACES] Генерируем данные о доступности для {gis_place['name']}")
            accessibility_data = self.accessibility_generator.generate_accessibility_data(gis_place)
            
            self.storage.save_place_accessibility(place_id, accessibility_data)
        
        reviews_data = self.storage.get_place_reviews(place_id)
        if not reviews_data:
            reviews_data = self._generate_reviews(gis_place["name"])
            for review in reviews_data:
                self.storage.add_place_review(place_id, review)
        
        if filters:
            available_filters = {cond["filter_type"] for cond in accessibility_data["accessibility_conditions"]}
            if not all(f in available_filters for f in filters):
                return None
        place = Place(
            id=place_id,
            name=gis_place["name"],
            location=PlaceLocation(
                latitude=gis_place["latitude"],
                longitude=gis_place["longitude"]
            ),
            accessibility_conditions=accessibility_data["accessibility_conditions"],
            reviews=[Review(**review) for review in reviews_data],
            overall_rating=accessibility_data["overall_rating"]
        )
        
        return place
    
    def _create_bbox(self, lat: float, lon: float, radius_km: float = 5.0) -> Tuple[float, float, float, float]:
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * 0.6)
        
        return (
            lat - lat_offset,
            lon - lon_offset,
            lat + lat_offset,
            lon + lon_offset
        )
    
    def _generate_reviews(self, place_name: str) -> List[Dict[str, Any]]:
        review_templates = [
            "Отличное место, очень доступно! Есть пандус и широкие проходы",
            "Хорошая атмосфера, но шумно. Нет индукционной петли",
            "Прекрасное обслуживание, рекомендую. Все условия доступности соблюдены",
            "Уютно и тихо, идеально для работы. Мягкое освещение, низкий уровень шума",
            "Дорого, но качественно. Есть аудиогиды и Брайль"
        ]
        
        reviews = []
        num_reviews = 3
        
        for i in range(num_reviews):
            review = {
                "author": f"{['Анна', 'Михаил', 'Елена', 'Дмитрий', 'Ольга'][i]} {['С.', 'М.', 'К.', 'В.', 'П.'][i]}",
                "rating": 4 + (i % 2),
                "text": review_templates[i % len(review_templates)]
            }
            reviews.append(review)
        
        return reviews
    
    async def _get_mock_places(self, request: PlaceSearchRequest) -> PlaceSearchResponse:
        filter_values = [f.value for f in request.filters] if request.filters else []
        mock_places = self.mock_generator.generate_mock_places(
            query=request.query,
            location=(request.location.latitude, request.location.longitude),
            filters=filter_values
        )
        
        places = []
        for mock_place in mock_places:
            place = Place(**mock_place)
            places.append(place)
        
        return PlaceSearchResponse(places=places)
    
    async def add_review(self, request: AddReviewRequest) -> bool:
        place_id = request.place_id
        
        review_data = {
            "author": request.author,
            "rating": request.overall_rating,
            "text": request.text
        }
        
        success = self.storage.add_place_review(place_id, review_data)
        
        if not success:
            return False
        
        await self._update_accessibility_from_review(place_id, request.accessibility_ratings)
        
        return True
    
    async def _update_accessibility_from_review(self, place_id: str, ratings: List[AccessibilityRating]) -> None:
        current_data = self.storage.get_place_accessibility(place_id)
        
        if not current_data:
            all_ratings = {}
        else:
            all_ratings = current_data.get("all_ratings", {})
        
        for rating in ratings:
            if rating.rating > 0:
                filter_type = rating.filter_type.value
                if filter_type not in all_ratings:
                    all_ratings[filter_type] = []
                all_ratings[filter_type].append(rating.rating)
        
        accessibility_conditions = []
        for filter_type, rating_list in all_ratings.items():
            if rating_list:
                average_rating = sum(rating_list) / len(rating_list)
                condition = {
                    "filter_type": filter_type,
                    "name": self.accessibility_generator._get_condition_name(filter_type),
                    "rating": round(average_rating, 1)
                }
                accessibility_conditions.append(condition)
        
        new_data = {
            "accessibility_conditions": accessibility_conditions,
            "all_ratings": all_ratings,
            "overall_rating": self.accessibility_generator._calculate_overall_rating(accessibility_conditions)
        }
        
        self.storage.save_place_accessibility(place_id, new_data)
    
