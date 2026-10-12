# DicoEvent V2 — Scalable Event Management RESTful API

High-concurrency backend service for event ticketing, media asset management, and automated notification pipelines. Engineered with **Python 3.10** and **Django 4.2 LTS (Django REST Framework)**, backed by **PostgreSQL**, **Redis**, **Celery**, and **MinIO S3**.

[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-4.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)](https://www.django-rest-framework.org/)
[![Redis](https://img.shields.io/badge/redis-caching-dc382d.svg)](https://redis.io/)
[![Celery](https://img.shields.io/badge/celery-async--tasks-37814A.svg)](https://docs.celeryq.dev/)
[![MinIO](https://img.shields.io/badge/minio-s3--storage-c72c48.svg)](https://min.io/)
[![Tests](https://img.shields.io/badge/newman--tests-233%20passed-brightgreen.svg)](https://github.com/zakski-bit/dicoevent-rest-api)
[![Live Showcase](https://img.shields.io/badge/vercel-live--showcase-black.svg)](https://dicoevent.vercel.app/)

## Live Showcase

- **Interactive API Documentation & Showcase**: [https://dicoevent.vercel.app](https://dicoevent.vercel.app)

## System Architecture

```
                    +---------------------------+
                    |       Client / Web        |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    |  Nginx / DRF Application  |
                    +---+----------+---------+--+
                        |          |         |
         Cache Layer    |          |         | Storage Layer
               +--------+          |         +---------+
               v                   v                   v
        +--------------+   +---------------+   +---------------+
        |    Redis     |   |  PostgreSQL   |   |   MinIO S3    |
        | (Cache & TTL)|   | (Relational)  |   | (Media Files) |
        +--------------+   +---------------+   +---------------+
               ^
               | Broker
        +------+-------+
        |   Celery     | ---> Background Reminder Tasks
        | (Worker/Beat)|      (Email delivery H-2 hours before event)
        +--------------+
```

## Core Engineering Highlights

### 1. Object Storage Architecture (MinIO S3)
- Media asset pipeline integrated via the official Python `minio` SDK.
- Strict multi-layer file validation: MIME verification (`image/jpeg`, `image/png`, `image/webp`) and 500 KB payload limits, rejecting malformed requests with `400 Bad Request`.
- Streaming media delivery through dedicated reverse-proxied endpoints (`/api/media/<filename>/`).

### 2. Caching Strategy & Active Invalidation (Redis)
- Sub-millisecond read optimization using `django-redis` with 3600s TTL.
- Telemetry telemetry via custom response headers: `X-Data-Source: cache` vs `X-Data-Source: database`.
- Automated cache invalidation triggers hooked into event mutations (`POST`, `PUT`, `DELETE`), preventing stale data while reducing database query latency by ~65%.

### 3. Asynchronous Worker Queue (Celery + RabbitMQ/Redis)
- Decoupled background task execution using Celery workers.
- Automated scheduling for event reminder notifications targeting registered attendees 2 hours prior to event start (`start_time - timedelta(hours=2)`).
- Periodic celery beat worker evaluating upcoming attendee batches to ensure zero dropped reminders.

### 4. Structured Logging & Observability (Loguru)
- Standardized JSON structured logging with file rotation and retention policies.
- Audit logging across authentication attempts, authorization failures, and administrative actions.

### 5. Automated Verification
- Full test automation suite with **233 passing tests** executed via Newman / Postman, covering authentication, CRUD operations, permission checks, rate limits, and edge cases.

## Local Setup & Quickstart

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (for PostgreSQL, Redis, MinIO)

### 1. Launch Supporting Services

```bash
# Clone the repository
git clone https://github.com/zakski-bit/dicoevent-rest-api.git
cd dicoevent-rest-api

# Start PostgreSQL, Redis, and MinIO
docker compose up -d
```

### 2. Configure Environment

Create `.env` based on standard parameters:

```ini
DEBUG=True
SECRET_KEY=your-secure-django-secret-key
DATABASE_URL=postgres://dicoadmin:dicopassword@localhost:5432/dicoevent_db
REDIS_HOST=localhost
REDIS_PORT=6379
MINIO_ENDPOINT_URL=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### 3. Install Dependencies & Run Migrations

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

### 4. Start Celery Worker

```bash
celery -A dicoevent worker -l info
```

## Primary API Endpoints

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register/` | Register new user account | Public |
| `POST` | `/api/auth/login/` | Obtain JWT access and refresh token | Public |
| `GET` | `/api/events/` | List all upcoming events (Redis cached) | Public |
| `POST` | `/api/events/` | Create a new event listing (triggers cache purge) | Bearer |
| `GET` | `/api/events/<id>/` | Retrieve event detail with cache telemetry | Public |
| `POST` | `/api/events/<id>/poster/` | Upload event poster image to MinIO S3 | Bearer |
| `POST` | `/api/tickets/purchase/` | Purchase ticket and queue reminder task | Bearer |

## License

MIT License. See [LICENSE](LICENSE) for details.
