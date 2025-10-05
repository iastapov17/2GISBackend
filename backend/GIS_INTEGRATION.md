# Интеграция с 2GIS API для слоя освещённости

## 📋 Обзор

Для слоя **"light" (освещённость)** реализована динамическая загрузка данных из [2GIS Places API](https://docs.2gis.com/ru/api/search/places/reference/3.0/items).

### Логика работы:

1. **Поиск торговых центров** в заданном bbox через 2GIS API
2. **Извлечение координат** (items.point) для каждого ТЦ
3. **Создание полигонов** (круги радиусом 100м) вокруг ТЦ
4. **Возврат полигонов** с метриками освещённости

### Почему торговые центры?

- ТЦ обычно **хорошо освещены** как внутри, так и снаружи
- Вокруг ТЦ есть **уличное освещение** для безопасности посетителей
- Данные доступны через **2GIS API** в реальном времени

---

## 🔧 Архитектура

### 1. `GisService` (app/services/gis_service.py)

Отвечает за взаимодействие с 2GIS Places API:

```python
class GisService:
    async def get_shopping_centers(bbox) -> List[Dict]:
        """Получить ТЦ из 2GIS API"""
        # GET https://catalog.api.2gis.com/3.0/items
        # params: q="торговый центр", viewpoint1, viewpoint2
        
    def create_polygon_around_point(lat, lon, radius_m=100) -> List[List[float]]:
        """Создать круглый полигон вокруг точки"""
        # Генерирует 16 точек для аппроксимации круга
        
    async def get_light_polygons(bbox) -> List[Dict]:
        """Комбинирует два метода выше"""
```

### 2. `PolygonLoader` (app/data/polygon_loader.py)

Загружает данные из разных источников:

```python
class PolygonLoader:
    def __init__(self, gis_service=None):
        # Для света: приоритет 2GIS API, fallback JSON файл
        
    async def find_polygons_in_bbox_async(layer_type, bbox):
        """
        Асинхронный поиск полигонов:
        - light: сначала 2GIS, потом файл
        - остальные: только файлы
        """
```

### 3. `MockDataGenerator` (app/data/mock_data.py)

Генерирует или загружает данные:

```python
class MockDataGenerator:
    def __init__(self, gis_service=None):
        self.polygon_loader = get_polygon_loader(gis_service)
        
    async def generate_segments_in_bbox_async(layer_type, bbox):
        """
        Для света: использует polygon_loader.find_polygons_in_bbox_async
        """
```

### 4. `MapService` (app/services/map_service.py)

Главный сервис для работы со слоями:

```python
class MapService:
    def __init__(self):
        self.gis_service = get_gis_service()
        self.mock_generator = MockDataGenerator(gis_service=self.gis_service)
        
    async def get_layer_data(layer_type, bbox):
        """
        Для света: вызывает generate_segments_in_bbox_async
        Для остальных: синхронный метод
        """
```

---

## 🚀 Использование

### API Endpoint

```bash
GET /api/v1/layers/light?bbox=55.75,37.61,55.76,37.63
```

### Что происходит внутри:

1. MapService получает запрос на слой "light"
2. Вызывает MockDataGenerator.generate_segments_in_bbox_async("light", bbox)
3. Тот вызывает PolygonLoader.find_polygons_in_bbox_async("light", bbox)
4. PolygonLoader вызывает GisService.get_light_polygons(bbox)
5. GisService:
   - Делает запрос к 2GIS API: `GET /3.0/items?q=торговый центр&...`
   - Получает список ТЦ с координатами
   - Для каждого ТЦ создаёт полигон радиусом 100м
6. Возвращает полигоны с метриками:
   ```json
   {
     "id": "light_tc_12345",
     "coordinates": [[lon, lat], ...],
     "street_name": "ТЦ Атриум",
     "metrics": {
       "light_lux": 180.0,  // Хорошее освещение
       "noise_db": 65.0,
       "crowd_level": 4
     }
   }
   ```

---

## 🎯 Параметры 2GIS API

### Запрос к /3.0/items

```
GET https://catalog.api.2gis.com/3.0/items
```

**Параметры:**

| Параметр | Описание | Пример |
|----------|----------|--------|
| `q` | Поисковый запрос | `торговый центр` |
| `region_id` | ID региона | `1` (Москва) |
| `viewpoint1` | Левая нижняя точка bbox | `37.61,55.75` |
| `viewpoint2` | Правая верхняя точка bbox | `37.63,55.76` |
| `type` | Тип объектов | `branch` |
| `fields` | Поля для возврата | `items.point` |
| `page_size` | Кол-во результатов | `50` |
| `key` | API ключ (опц.) | `ваш_ключ` |

### Ответ

```json
{
  "result": {
    "items": [
      {
        "id": "70000001234567",
        "name": "ТЦ Атриум",
        "point": {
          "lat": 55.753,
          "lon": 37.621
        }
      }
    ]
  }
}
```

---

## 🔐 API Ключ (опционально)

Для production рекомендуется получить API ключ:

### Как добавить:

1. **В конфигурацию** (app/core/config.py):
   ```python
   class Settings(BaseSettings):
       gis_api_key: Optional[str] = None
   ```

2. **В .env**:
   ```
   GIS_API_KEY=your_api_key_here
   ```

3. **В GisService**:
   ```python
   from app.core.config import settings
   
   class GisService:
       def __init__(self):
           self.api_key = settings.gis_api_key
   ```

---

## 🛠️ Настройка

### Радиус полигона

По умолчанию 100 метров. Можно изменить:

```python
# app/services/gis_service.py
def create_polygon_around_point(
    lat, lon, 
    radius_m: int = 150,  # ← Изменить здесь
    num_points: int = 16
)
```

### Метрики света

По умолчанию для ТЦ устанавливается 180 lux:

```python
# app/services/gis_service.py
polygons.append({
    "metrics": {
        "light_lux": 180.0,  # ← Изменить здесь
        # ...
    }
})
```

### Fallback на файл

Если 2GIS API недоступен, используется файл:

```
backend/app/data/polygons_light.json
```

---

## 🧪 Тестирование

### 1. Запустить сервер

```bash
cd backend
/usr/bin/python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Проверить слой света (Москва)

```bash
curl "http://localhost:8000/api/v1/layers/light?bbox=55.75,37.61,55.76,37.63"
```

### 3. Проверить логи

```
✅ [LIGHT] Будет использоваться 2GIS API для поиска ТЦ
✅ [2GIS] Найдено 15 торговых центров
✅ [2GIS] Создано 15 полигонов освещённости из ТЦ
✅ [LIGHT] Используем 15 реальных полигонов
```

### 4. Если 2GIS недоступен:

```
⚠️ [LIGHT] Ошибка загрузки из 2GIS, используем fallback
⚙️ [LIGHT] Генерируем 30 синтетических полигонов
```

---

## 📊 Производительность

- **Время запроса к 2GIS**: ~200-500ms
- **Количество ТЦ в Москве (центр)**: 15-50 шт
- **Размер ответа**: ~10-50 KB

### Оптимизация:

1. **Кеширование** результатов на N минут
2. **Ограничение** `page_size` до 50
3. **Таймаут** запроса 10 секунд

---

## 🐛 Отладка

### Проверить что 2GIS отвечает:

```bash
curl "https://catalog.api.2gis.com/3.0/items?q=торговый%20центр&region_id=1&viewpoint1=37.61,55.75&viewpoint2=37.63,55.76&type=branch&fields=items.point&page_size=10"
```

### Логи при старте:

```python
# Должны увидеть:
✅ [NOISE] Загружено 14554 полигонов из app/data/polygons_noise.json
✅ [LIGHT] Будет использоваться 2GIS API для поиска ТЦ
⚠️ [CROWD] Файл не найден: app/data/polygons_crowd.json
⚠️ [PUDDLES] Файл не найден: app/data/polygons_puddles.json
```

---

## 📚 Дополнительно

### Документация 2GIS

- [Places API Reference](https://docs.2gis.com/ru/api/search/places/reference/3.0/items)
- [Поиск мест](https://docs.2gis.com/ru/api/search/places/overview)

### Альтернативы

Вместо ТЦ можно искать:
- **Остановки транспорта** (хорошо освещены)
- **Банкоматы** (обычно с подсветкой)
- **Парковки** (освещение для безопасности)

Изменить в `GisService.get_shopping_centers()`:

```python
params = {
    "q": "остановка",  # ← Изменить запрос
    # ...
}
```

---

## ✅ Итого

🎉 Теперь слой света использует **реальные данные** из 2GIS API!

- ✅ Автоматический поиск торговых центров
- ✅ Создание полигонов освещённости вокруг ТЦ
- ✅ Fallback на файл при недоступности API
- ✅ Асинхронная загрузка для производительности

