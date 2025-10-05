from typing import List, Tuple, Optional, Dict
from datetime import datetime
from app.schemas.map_layers import (
    LayerType, 
    SegmentFeature,
    Geometry,
)
from app.data.mock_data import MockDataGenerator
from app.services.gis_service import get_gis_service


class MapService:
    
    def __init__(self):
        self.gis_service = get_gis_service(api_key='49186240-cdc8-4f73-b64f-7933d62178ae')
        self.mock_generator = MockDataGenerator(gis_service=self.gis_service)
    
    async def get_layer_data(
        self,
        layer_type: LayerType,
        bbox: Tuple[float, float, float, float],
        time: Optional[datetime] = None
    ) -> List[SegmentFeature]:
        if layer_type == LayerType.LIGHT:
            segments = await self.mock_generator.generate_segments_in_bbox_async(
                bbox=bbox,
                layer_type=layer_type.value
            )
        else:
            segments = self.mock_generator.generate_segments_in_bbox(
                bbox=bbox,
                layer_type=layer_type.value
            )
        
        features = []
        for segment in segments:
            value, level, color = self._get_layer_metrics(
                segment, 
                layer_type, 
                time
            )
            
            feature = SegmentFeature(
                segment_id=segment["id"],
                geometry=Geometry(
                    type="Polygon",
                    coordinates=segment["geometry"]["coordinates"]
                ),
                value=value,
                level=level,
                color=color,
                street_name=segment.get("street_name"),
                confidence=segment.get("confidence", 0.8),
                last_updated=segment.get("last_updated", datetime.utcnow())
            )
            features.append(feature)
        
        return features
    
    async def get_all_layers(
        self,
        layer_types: List[LayerType],
        bbox: Tuple[float, float, float, float],
        time: Optional[datetime] = None
    ) -> Dict[str, List[SegmentFeature]]:
        result = {}
        
        for layer_type in layer_types:
            if layer_type == LayerType.LIGHT:
                segments = await self.mock_generator.generate_segments_in_bbox_async(
                    bbox=bbox,
                    layer_type=layer_type.value
                )
            else:
                segments = self.mock_generator.generate_segments_in_bbox(
                    bbox=bbox,
                    layer_type=layer_type.value
                )
            
            features = []
            
            for segment in segments:
                value, level, color = self._get_layer_metrics(
                    segment, 
                    layer_type, 
                    time
                )
                
                feature = SegmentFeature(
                    segment_id=segment["id"],
                    geometry=Geometry(
                        type="Polygon",
                        coordinates=segment["geometry"]["coordinates"]
                    ),
                    value=value,
                    level=level,
                    color=color,
                    street_name=segment.get("street_name"),
                    confidence=segment.get("confidence", 0.8),
                    last_updated=segment.get("last_updated", datetime.utcnow())
                )
                features.append(feature)
            
            result[layer_type.value] = features
        
        return result
    
    def _get_layer_metrics(
        self, 
        segment: dict, 
        layer_type: LayerType,
        time: Optional[datetime]
    ) -> Tuple[float, str, str]:
        metrics = segment["metrics"]
        
        if layer_type == LayerType.NOISE:
            noise_db = metrics["noise_db"]
            return (
                noise_db,
                self._get_noise_level(noise_db),
                self._get_noise_color(noise_db)
            )
        
        elif layer_type == LayerType.CROWD:
            crowd = metrics["crowd_level"]
            if time and time.hour in [8, 9, 17, 18, 19]:
                crowd = min(5, crowd + 1)
            return (
                crowd,
                self._get_crowd_level(crowd),
                self._get_crowd_color(crowd)
            )
        
        elif layer_type == LayerType.LIGHT:
            light_lux = metrics["light_lux"]
            return (
                light_lux,
                self._get_light_level(light_lux),
                self._get_light_color(light_lux)
            )
        
        elif layer_type == LayerType.PUDDLES:
            puddles = metrics.get("puddles", False)
            return (
                1.0 if puddles else 0.0,
                "has_puddles" if puddles else "no_puddles",
                "#EF4444" if puddles else "#22C55E"
            )
    
    def _get_noise_level(self, db: float) -> str:
        if db < 60:
            return "low"
        elif db < 70:
            return "medium"
        elif db < 80:
            return "high"
        else:
            return "extreme"
    
    def _get_noise_color(self, _) -> str:
        return "#FFA07A"
    
    def _get_crowd_level(self, level: float) -> str:
        if level <= 2:
            return "low"
        elif level <= 3:
            return "medium"
        elif level <= 4:
            return "high"
        else:
            return "extreme"
    
    def _get_crowd_color(self, level: float) -> str:
        return "#FFFACD"
    
    def _get_light_level(self, lux: float) -> str:
        if lux < 50:
            return "dark"
        elif lux < 150:
            return "dim"
        else:
            return "bright"
    
    def _get_light_color(self, lux: float) -> str:
        return "#ADD8E6"

