# TestDocker

Минималистичный FastAPI-сервис для хранения и получения постов с PostgreSQL в контейнерах Docker.

## Цель проекта

Это простое API для CRUD-операций над публикациями:
- создание поста;
- получение списка постов;
- проверка состояния сервиса;
- работа через Docker Compose с PostgreSQL.

Проект подходит для демонстрации базовой архитектуры Python-сервиса, контейнеризации и работы с БД.

## Архитектура

- Backend: FastAPI
- ORM: SQLAlchemy
- База данных: PostgreSQL 16
- Контейнеризация: Docker + Docker Compose
- API-сервис запускается в контейнере `app`
- БД запускается в контейнере `db`

## Стек технологий

- Python 3.13
- FastAPI
- Uvicorn
- SQLAlchemy
- psycopg2-binary
- PostgreSQL

## Структура проекта

```text
TestDocker/
├── apps/
│   ├── __init__.py
│   ├── database.py        # подключение к PostgreSQL и инициализация БД
│   ├── main.py            # FastAPI приложение и endpoints
│   ├── models.py          # SQLAlchemy-модель Post
│   └── schemas.py         # Pydantic-схемы
├── init/
│   └── 01_init_posts.sql # инициализация таблицы posts
├── Dockerfile             # сборка Python-сервиса
├── docker-compose.yml     # запуск app + PostgreSQL
├── requirements.txt       # Python-зависимости
├── README.md              # документация проекта
└── .gitignore             # (если добавлен в проект)
```

## Запуск проекта

### 1. Клонировать проект

```bash
git clone <repository-url>
cd TestDocker
```

### 2. Запустить через Docker Compose

```bash
docker compose up --build
```

После запуска:
- API будет доступно по адресу: http://localhost:8000
- PostgreSQL будет доступна на: localhost:5433

## Проверка сервиса

### Health check

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ:

```json
{"status": "ok"}
```

### Корневой endpoint

```bash
curl http://localhost:8000/
```

Возвращает информацию о версии приложения и времени отклика.

## API endpoints

### Получить список постов

```bash
curl "http://localhost:8000/posts?limit=10"
```

### Создать пост

```bash
curl -X POST http://localhost:8000/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My first post",
    "content": "Some content"
  }'
```

## Переменные окружения

Основная переменная задаётся через `docker-compose.yml`:

```env
DATABASE_URL=postgresql://app_user:app_pass@db:5432/app_db
```

## База данных

В контейнере PostgreSQL создаётся база `app_db`, пользователь `app_user` и пароль `app_pass`.

Таблица `posts` создаётся автоматически при запуске приложения и инициализируется SQL-скриптом из `init/01_init_posts.sql`.

## Основные команды

```bash
# Запуск
 docker compose up --build

# Остановка
 docker compose down

# Пересборка без кэша
 docker compose up --build --force-recreate

# Просмотр логов
 docker compose logs -f app
```

## Итог

Этот проект демонстрирует основу backend-архитектуры на FastAPI с PostgreSQL и Docker Compose. Он подходит как базовая заготовка для портфолио и дальнейшего развития в сторону более сложного сервиса.
