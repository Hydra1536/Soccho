# Soccho Render Deployment Guide (HTTP-Only)

This repository is now configured for HTTP-only service communication.

## 1. Important repo rule

Keep each Render service rooted at the repository root.

Do not set a Render `rootDir` like `auth/` or `gateway/` because this monorepo uses shared files outside service folders.

## 2. Recommended Render service layout

### Public services

- `soccho-frontend` (Static Site)
- `soccho-gateway` (Web Service)
- `soccho-notification` (Web Service)
- `soccho-admin` (Web Service)

### Internal HTTP services

- `soccho-auth-http` (Web Service)
- `soccho-social-http` (Web Service)
- `soccho-transaction-http` (Web Service)

### Background worker

- `soccho-transaction-worker` (Background Worker)

### Managed data services

- Render Postgres
- Render Key Value (Redis)

## 3. Exact commands per service

All commands below assume the service root is the repository root.

### soccho-frontend

- Build Command:
```bash
cd frontend && npm install && npm run build
```
- Publish Directory:
```bash
frontend/dist
```

Add SPA rewrite:
- Source: `/*`
- Destination: `/index.html`
- Action: `Rewrite`

### soccho-gateway

- Build Command:
```bash
pip install -r gateway/requirements.txt
```
- Start Command:
```bash
cd gateway && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### soccho-notification

- Build Command:
```bash
pip install -r notification/requirements.txt
```
- Pre-Deploy Command:
```bash
cd notification && python manage.py migrate
```
- Start Command:
```bash
cd notification && daphne -b 0.0.0.0 -p $PORT notification_service.asgi:application
```

### soccho-admin

- Build Command:
```bash
pip install -r admin/requirements.txt
```
- Pre-Deploy Command:
```bash
cd admin && python manage.py migrate
```
- Start Command:
```bash
cd admin && gunicorn admin_service.wsgi --bind 0.0.0.0:$PORT
```

### soccho-auth-http

- Build Command:
```bash
pip install -r auth/requirements.txt
```
- Pre-Deploy Command:
```bash
cd auth && python manage.py migrate
```
- Start Command:
```bash
cd auth && gunicorn auth_service.wsgi --bind 0.0.0.0:$PORT
```

### soccho-social-http

- Build Command:
```bash
pip install -r social/requirements.txt
```
- Pre-Deploy Command:
```bash
cd social && python manage.py migrate
```
- Start Command:
```bash
cd social && gunicorn social_service.wsgi --bind 0.0.0.0:$PORT
```

### soccho-transaction-http

- Build Command:
```bash
pip install -r transaction/requirements.txt
```
- Pre-Deploy Command:
```bash
cd transaction && python manage.py migrate
```
- Start Command:
```bash
cd transaction && gunicorn transaction_service.wsgi --bind 0.0.0.0:$PORT
```

### soccho-transaction-worker

- Build Command:
```bash
pip install -r transaction/requirements.txt
```
- Start Command:
```bash
cd transaction && celery -A transaction_service worker -B
```

## 4. Required environment variables

Set these service URLs in `soccho-gateway`:

- `AUTH_HTTP_BASE_URL`
- `SOCIAL_HTTP_BASE_URL`
- `TRANSACTION_HTTP_BASE_URL`
- `NOTIFICATION_HTTP_BASE_URL`

Set these shared values across backend services:

- `DATABASE_URL`
- `REDIS_CACHE_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `CHANNEL_LAYERS_REDIS_URL`
- `ALLOWED_ORIGINS`
- `AUTH_SECRET_KEY`
- `SOCIAL_SECRET_KEY`
- `TRANSACTION_SECRET_KEY`
- `NOTIFICATION_SECRET_KEY`
- `ADMIN_SECRET_KEY`
- `GATEWAY_SECRET_KEY`
- `AES_SECRET_KEY`

Important: `AUTH_SECRET_KEY` must be identical in `soccho-auth-http`, `soccho-gateway`, and `soccho-notification`.

## 5. Post-deploy verification

- `https://soccho-gateway.onrender.com/healthz` returns 200.
- Login succeeds and frontend receives access/refresh tokens.
- Home page loads summary/friends without 401 loops.
