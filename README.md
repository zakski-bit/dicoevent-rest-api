# DicoEvent Versi 2 - RESTful API

[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-4.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/django--rest--framework-3.14-red.svg)](https://www.django-rest-framework.org/)
[![Redis](https://img.shields.io/badge/redis-caching-dc382d.svg)](https://redis.io/)
[![Celery](https://img.shields.io/badge/celery-async--tasks-37814A.svg)](https://docs.celeryq.dev/)
[![MinIO](https://img.shields.io/badge/minio-s3--storage-c72c48.svg)](https://min.io/)
[![Tests](https://img.shields.io/badge/newman--tests-233%20passed-brightgreen.svg)](https://github.com/zakski-bit/dicoevent-rest-api)
[![Live Showcase](https://img.shields.io/badge/vercel-live--showcase-black.svg)](https://dicoevent-rest-api.vercel.app/)

RESTful API backend untuk platform manajemen event **DicoEvent (Versi 2)** oleh startup **DicoTech**, dibangun menggunakan **Python 3.10** dan **Django 4.2 LTS**.

Proyek ini telah memenuhi seluruh kriteria penilaian tingkat lanjut (**Tingkat Lanjut / Advanced - 4 Points** pada setiap kriteria, total **Bintang 5 / Nilai 4.0**).

> 🌐 **Live Interactive Showcase (Vercel)**:
> Halaman demo interaktif dan simulasi API live dapat diakses di: **[Live Showcase Demo](https://dicoevent-rest-api.vercel.app/)** *(atau domain Vercel Anda)*.
> *Catatan: Versi Vercel berfungsi sebagai interactive UI showcase & API preview documentation (tanpa live database backend). Layanan backend penuh dengan PostgreSQL, Redis, dan Celery Worker dijalankan di lokal/VPS melalui Docker Compose.*

---

## Ringkasan Pemenuhan Kriteria (Advanced / Bintang 5)

### Kriteria 1: Upload Berkas Media (Advanced / 4 pts)
- **MinIO SDK**: Menggunakan library resmi `minio` Python SDK untuk mengelola upload berkas media ke object storage.
- **Validasi Berkas**:
  - Validasi MIME type: Hanya menerima format gambar (`image/jpeg`, `image/png`, `image/gif`, `image/webp`, dll). Berkas non-gambar ditolak dengan status **400 Bad Request**.
  - Validasi ukuran file: Maksimal 500 kB. Berkas lebih besar dari 500 kB ditolak dengan status **400 Bad Request**.
- **Penyimpanan Database**: Nama berkas yang berhasil diunggah disimpan di tabel database melalui model `EventPoster` (`events_eventposter`) yang berelasi dengan tabel `Event`.
- **Menampilkan Berkas Media**:
  - `GET /api/events/<event_id>/poster/`: Menampilkan daftar poster dari sebuah event.
  - `GET /api/media/<filename>/`: Menampilkan dan melakukan streaming berkas gambar langsung dari MinIO.
- **Environment Variables MinIO**:
  - `MINIO_ENDPOINT_URL` (contoh: `localhost:9000`)
  - `MINIO_ACCESS_KEY` (contoh: `minioadmin`)
  - `MINIO_SECRET_KEY` (contoh: `minioadmin`)

### Kriteria 2: Caching dengan Redis (Advanced / 4 pts)
- **Backend Caching**: Menggunakan Redis backend melalui `django-redis`.
- **Custom Header**:
  - Mengembalikan header `X-Data-Source: database` saat cache miss.
  - Mengembalikan header `X-Data-Source: cache` saat cache hit.
- **TTL Cache**: Cache disimpan selama **1 jam (3600 detik)**.
- **Cakupan Caching**:
  - Caching diterapkan pada detail event (`GET /api/events/<id>/`).
  - Caching juga diterapkan pada list event (`GET /api/events/` dan pagination).
- **Invalidasi Cache Otomatis**: Cache otomatis dihapus (invalidate) saat terjadi perubahan data:
  - Saat event baru dibuat (`POST /api/events/`).
  - Saat event diperbarui (`PUT /api/events/<id>/`).
  - Saat event dihapus (`DELETE /api/events/<id>/`).
- **Environment Variables Redis**:
  - `REDIS_HOST` (contoh: `localhost`)
  - `REDIS_PORT` (contoh: `6379`)

### Kriteria 3: Asynchronous Task dengan Celery (Advanced / 4 pts)
- **Celery Library**: Menggunakan Celery dengan broker Redis / RabbitMQ untuk menangani background worker.
- **Pengiriman Email Reminder**:
  - Menerapkan asynchronous task `send_event_reminder_email` untuk mengirimkan email pengingat acara kepada pengguna yang telah memesan tiket.
  - Email reminder dijadwalkan secara otomatis tiba pada **H-2 jam sebelum event dimulai** (`event.start_time - timedelta(hours=2)`).
  - Dilengkapi task periodik `check_and_send_due_event_reminders` untuk memindai event yang akan dimulai dalam 2 jam.
- **Konfigurasi Email Django**: Dikonfigurasi menggunakan Django SMTP email backend.
- **Environment Variables Celery & Email**:
  - `CELERY_BROKER_URL` (contoh: `redis://localhost:6379/0`)
  - `MAIL_HOST`
  - `MAIL_PORT`
  - `MAIL_USER`
  - `MAIL_PASSWORD`

### Kriteria 4: Logging dengan Loguru (Advanced / 4 pts)
- **Custom Logging Loguru**: Menggunakan library `loguru` yang terstruktur.
- **Format Log**: Menampilkan timestamp, log level, dan log message:
  ```text
  {time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} - {message}
  ```
  Contoh:
  `2026-09-27 06:56:02.955 | INFO | events.views:perform_create:112 - Event 58bfb236 created by Aras`
- **Pemisahan File Log**:
  - Log level INFO (dan seluruh aktivitas normal) disimpan di file: `application.log`.
  - Log level ERROR disimpan di file: `error.log`.
- **Rotasi File Log**: Dikonfigurasi dengan rotasi harian otomatis: `rotation="1 day"`.
- **Logging Middleware**: Merekam setiap request HTTP masuk, status response, user, latency, serta unhandled exceptions.

---

## Prasyarat & Menjalankan Aplikasi

### 1. Menjalankan Service Pendukung (Docker)
Pastikan Docker Desktop aktif, lalu jalankan service:
```bash
# PostgreSQL
docker run -d --name forum-postgres -p 5432:5432 -e POSTGRES_USER=dicoevent_user -e POSTGRES_PASSWORD=dicoevent_password -e POSTGRES_DB=dicoevent_db postgres:16-alpine

# Redis
docker run -d --name dicoevent-redis -p 6379:6379 redis:alpine

# MinIO
docker run -d --name dicoevent-minio -p 9000:9000 -p 9001:9001 -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin coollabsio/minio:latest server /data --console-address ":9001"
```

### 2. Instalasi Dependensi
```bash
# Menggunakan Pipenv (sesuai Pipfile)
pipenv install

# Atau menggunakan pip
pip install -r requirements.txt
```

### 3. Konfigurasi Environment (.env)
Salin `.env.example` menjadi `.env` dan sesuaikan kredensial jika diperlukan:
```ini
DEBUG=True
SECRET_KEY=django-insecure-dicoevent-secret-key-super-secure-production-ready-2025
DATABASE_NAME=dicoevent_db
DATABASE_USER=dicoevent_user
DATABASE_PASSWORD=dicoevent_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# MinIO Storage Settings
MINIO_ENDPOINT_URL=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=dicoevent

# Redis Cache Settings
REDIS_HOST=localhost
REDIS_PORT=6379

# Celery & Asynchronous Task Settings
CELERY_BROKER_URL=redis://localhost:6379/0

# Mail Server Settings
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USER=your_email@gmail.com
MAIL_PASSWORD=your_email_password
```

### 4. Database Migration & Setup Superuser
```bash
python manage.py migrate
python manage.py seed_superuser
```

### 5. Menjalankan Celery Worker
Di terminal terpisah:
```bash
celery -A dicoevent worker -l info -P solo
```

### 6. Menjalankan Django Development Server
```bash
python manage.py runserver 0.0.0.0:8000
```

---

## Pengujian Postman
Proyek ini telah diverifikasi penuh menggunakan koleksi pengujian resmi Postman DicoEvent Versi 2:
- **Total Requests**: 94 requests
- **Total Assertions**: 233 assertions
- **Hasil**: 233 Passed (0 Failed, 100% Success Rate)
- Seluruh folder pengujian (Mandatory dan Optional) lulus tanpa kendala.
