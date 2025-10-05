# coding: utf-8
import json
import math
import random
from pathlib import Path


def create_circle_polygon(lon: float, lat: float, radius: float = 0.001) -> list:
    """
    Creates a circular polygon with 16 points around the center
    
    Args:
        lon: Longitude of center
        lat: Latitude of center  
        radius: Radius of circle in degrees (approximately 100 meters)
    
    Returns:
        List of 16 coordinate pairs forming a circle
    """
    
    coordinates = []
    for i in range(16):
        angle = 2 * math.pi * i / 16
        x = lon + radius * math.cos(angle)
        y = lat + radius * math.sin(angle)
        coordinates.append([x, y])
    
    return coordinates


def process_noise_data(input_file: str, output_file: str):
    print(f"Reading data from {input_file}...")
    
    with open(input_file, 'r', encoding='cp1251') as f:
        data = json.load(f)
    
    print(f"Found records: {len(data)}")
    
    polygons = []
    
    for item in data:
        try:
            lon = float(item['Longitude_WGS84'])
            lat = float(item['Latitude_WGS84'])
            
            coordinates = create_circle_polygon(lon, lat)
            
            noise_db = round(random.uniform(60, 100), 1)
            
            polygon = {
                "id": f"noise_{item['ID']}",
                "coordinates": coordinates,
                "metrics": {
                    "noise_db": noise_db,
                    "crowd_level": 0,
                    "light_lux": 0,
                    "snow_cleared": False
                }
            }
            
            polygons.append(polygon)
            
        except (KeyError, ValueError) as e:
            print(f"Error processing record ID={item.get('ID', 'unknown')}: {e}")
            continue
    
    result = {
        "polygons": polygons
    }
    
    print(f"Created polygons: {len(polygons)}")
    
    print(f"Saving result to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("Done!")


def main():
    script_dir = Path(__file__).parent
    
    input_file = script_dir / "data" / "data-2449-2025-09-25.json"
    output_file = script_dir / "data" / "noise_polygons.json"
    
    if not input_file.exists():
        print(f"Error: File {input_file} not found!")
        return
    
    process_noise_data(str(input_file), str(output_file))


if __name__ == "__main__":
    main()
