# Dostup.City API

API для построения доступных и тихих маршрутов в городе.

## Установка зависимостей

```bash
cd backend
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск сервиса

```bash
cd backend
source venv/bin/activate  # На Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Сервис будет доступен по адресу: http://localhost:8000

Документация API: http://localhost:8000/docs

## API Методы

### Основные эндпоинты

- `GET /` - Статус сервиса
- `GET /health` - Проверка здоровья сервиса

### Слои карты (`/api/v1/layers`)

- `GET /all` - Получить все слои карты (шум, толпа, освещение)
  - Параметры: bbox (границы), layers (типы слоев), time (время прогноза)

### Маршрутизация (`/api/v1/routes`)

- `POST /calm` - Построить тихий маршрут
  - Принимает: начальную и конечную точки, веса факторов

### Поиск мест (`/api/v1/places`)

- `GET /search` - Поиск мест по названию
  - Параметры: query (название), latitude, longitude, filters (фильтры доступности)
- `POST /reviews` - Добавить отзыв о месте

## Технологии

- FastAPI - веб-фреймворк
- GeoAlchemy2 - работа с геоданными
- Shapely - геометрические операции
- Uvicorn - ASGI сервер
