# Soccho Render Deployment Guide (HTTP-Only + Cold-Start Resilience)

This repository uses HTTP-only service communication and includes Render Free cold-start mitigation.

## 1. Important repo rule

Keep each Render service rooted at the repository root.

Do not set a Render `rootDir` like `auth/` or `gateway/` because this monorepo uses shared files outside service folders.

## 2. Render Free behavior and tradeoff

Render Free web services can spin down after ~15 minutes of inactivity and take time to wake.

Primary mitigation in this repo:

- gateway now returns controlled `503` for upstream warm-up failures (instead of opaque `502`),
- OAuth proxy has longer timeout and bounded retry.

Optional mitigation:

- keepalive worker can ping services periodically to reduce cold starts.

Tradeoff:

- keepalive reduces cold starts but consumes free instance hours and bandwidth.
- keepalive does not prevent platform maintenance or restart events.

## 3. Recommended Render service layout

### Public services

- `soccho-frontend` (Static Site)
- `soccho-gateway` (Web Service)
- `soccho-notification` (Web Service)
- `soccho-admin` (Web Service)

### Internal HTTP services

- `soccho-auth-http` (Web Service)
- `soccho-social-http` (Web Service)
- `soccho-transaction-http` (Web Service)

### Background workers

- `soccho-transaction-worker` (Background Worker)
- `soccho-keepalive-worker` (Background Worker, optional)

### Managed data services

- Render Postgres
- Render Key Value (Redis)

## 4. Exact commands per service

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

### soccho-keepalive-worker (optional)

- Build Command:
```bash
pip install -r keepalive/requirements.txt
```
- Start Command:
```bash
python keepalive/worker.py
```

## 5. Required environment variables

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

### Keepalive worker env (optional)

- `KEEPALIVE_ENABLED` (`true` or `false`)
- `KEEPALIVE_INTERVAL_SECONDS` (default `600`)
- `KEEPALIVE_TIMEOUT_SECONDS` (default `15`)
- `KEEPALIVE_JITTER_SECONDS` (default `0`)
- `KEEPALIVE_TARGETS` (comma-separated health URLs)

Default targets are:

- `https://soccho-gateway.onrender.com/healthz`
- `https://soccho-auth.onrender.com/api/auth/health/`
- `https://soccho-social.onrender.com/health/`
- `https://soccho-transaction.onrender.com/health/`
- `https://soccho-notification.onrender.com/health/`

## 6. Post-deploy verification

### Baseline checks

- `https://soccho-gateway.onrender.com/healthz` returns 200.
- `https://soccho-auth.onrender.com/api/auth/health/` returns 200.
- Login succeeds and frontend receives access/refresh tokens.
- Home page loads summary/friends without 401 loops.

### Cold-start checks

1. Let services idle for at least 15 minutes.
2. Attempt Google sign-in.
3. Confirm:
   - frontend shows wake-up messaging/retry flow instead of crashing,
   - gateway does not emit opaque `502` for OAuth warm-up path,
   - eventual redirect to Google works once auth is awake.

### Log checklist

- Gateway logs show structured upstream warm-up warnings on timeout/connection failures.
- OAuth retries are visible at most once per request path.
- Keepalive worker logs periodic probe results without process crash.
