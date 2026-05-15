# Soccho Render Microservice Deployment Guide

This guide is for deploying Soccho on Render as separate services.

## 1. Important repo rule

Keep each Render service rooted at the **repository root**.

Do **not** set a Render `rootDir` like `auth/` or `gateway/` for these services, because this repo uses shared files and folders outside each service directory, especially:

- `shared/proto/`
- `compile_protos.sh`
- repo-level env examples and deployment docs

If you set a subdirectory root, Render will not make files outside that root available to the service build/runtime.

## 2. Recommended Render service layout

Create these services:

### Public services

- `soccho-frontend` : Static Site
- `soccho-gateway` : Web Service
- `soccho-notification` : Web Service
- `soccho-admin` : Web Service

### Private internal HTTP services

- `soccho-auth-http` : Private Service
- `soccho-social-http` : Private Service
- `soccho-transaction-http` : Private Service

### Private internal gRPC services

- `soccho-auth-grpc` : Private Service
- `soccho-social-grpc` : Private Service
- `soccho-transaction-grpc` : Private Service
- `soccho-notification-grpc` : Private Service

### Background worker

- `soccho-transaction-worker` : Background Worker

### Managed data services

- Render Postgres
- Render Key Value (Redis)

## 3. Exact commands per service

All commands below assume the Render service root is the repo root.

### `soccho-frontend` (Static Site)

- Build Command:
```bash
cd frontend && npm install && npm run build
```
- Publish Directory:
```bash
frontend/dist
```

### `soccho-gateway` (Public Web Service)

- Build Command:
```bash
pip install -r gateway/requirements.txt
```
- Start Command:
```bash
cd gateway && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### `soccho-notification` (Public Web Service)

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

### `soccho-admin` (Public Web Service)

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

### `soccho-auth-http` (Private Service)

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

### `soccho-social-http` (Private Service)

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

### `soccho-transaction-http` (Private Service)

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

### `soccho-auth-grpc` (Private Service)

- Build Command:
```bash
pip install -r auth/requirements.txt
```
- Start Command:
```bash
cd auth && python manage.py run_grpc
```

### `soccho-social-grpc` (Private Service)

- Build Command:
```bash
pip install -r social/requirements.txt
```
- Start Command:
```bash
cd social && python manage.py run_grpc
```

### `soccho-transaction-grpc` (Private Service)

- Build Command:
```bash
pip install -r transaction/requirements.txt
```
- Start Command:
```bash
cd transaction && python manage.py run_grpc
```

### `soccho-notification-grpc` (Private Service)

- Build Command:
```bash
pip install -r notification/requirements.txt
```
- Start Command:
```bash
cd notification && python manage.py run_grpc
```

### `soccho-transaction-worker` (Background Worker)

- Build Command:
```bash
pip install -r transaction/requirements.txt
```
- Start Command:
```bash
cd transaction && celery -A transaction_service worker -B
```

## 4. Public URLs you will use

If you create the public services with these exact names, your public URLs will be:

- Frontend:
```text
https://soccho-frontend.onrender.com
```
- Gateway:
```text
https://soccho-gateway.onrender.com
```
- Notification WebSocket / public notification app:
```text
https://soccho-notification.onrender.com
```
- Admin:
```text
https://soccho-admin.onrender.com
```

Admin panel final URL:

```text
https://soccho-admin.onrender.com/<ADMIN_URL_PATH>
```

Example:

```text
https://soccho-admin.onrender.com/119115131318115/
```

## 5. Internal URLs and hostnames you will use

For private services, Render assigns an internal hostname. Copy each one from:

- Render Dashboard
- Service
- `Connect`
- `Internal`

Use those values in env vars.

### Gateway env mapping

Set these on `soccho-gateway`:

- `AUTH_HTTP_BASE_URL` = internal URL of `soccho-auth-http`
- `SOCIAL_HTTP_BASE_URL` = internal URL of `soccho-social-http`
- `TRANSACTION_HTTP_BASE_URL` = internal URL of `soccho-transaction-http`
- `NOTIFICATION_HTTP_BASE_URL` = internal URL of `soccho-notification`

- `AUTH_GRPC_HOST` = internal hostname of `soccho-auth-grpc` without scheme
- `AUTH_GRPC_PORT` = `8001`
- `SOCIAL_GRPC_HOST` = internal hostname of `soccho-social-grpc`
- `SOCIAL_GRPC_PORT` = `8002`
- `TRANSACTION_GRPC_HOST` = internal hostname of `soccho-transaction-grpc`
- `TRANSACTION_GRPC_PORT` = `8003`
- `NOTIFICATION_GRPC_HOST` = internal hostname of `soccho-notification-grpc`
- `NOTIFICATION_GRPC_PORT` = `8004`

### Social service env mapping

Set these on `soccho-social-http` and `soccho-social-grpc`:

- `AUTH_GRPC_HOST` = internal hostname of `soccho-auth-grpc`
- `AUTH_GRPC_PORT` = `8001`
- `TRANSACTION_GRPC_HOST` = internal hostname of `soccho-transaction-grpc`
- `TRANSACTION_GRPC_PORT` = `8003`

### Transaction service env mapping

Set these on `soccho-transaction-http`, `soccho-transaction-grpc`, and `soccho-transaction-worker`:

- `SOCIAL_GRPC_HOST` = internal hostname of `soccho-social-grpc`
- `SOCIAL_GRPC_PORT` = `8002`

### Notification service env mapping

Set these on `soccho-notification` and `soccho-notification-grpc`:

- `TRANSACTION_HTTP_BASE_URL` = internal URL of `soccho-transaction-http`

### Frontend env mapping

Set these on `soccho-frontend`:

- `VITE_API_URL` = public URL of `soccho-gateway`
- `VITE_GOOGLE_CLIENT_ID` = your Google OAuth client id
- `VITE_NOTIFICATION_WS_URL` = public URL of `soccho-notification`

## 6. Shared core env vars

Set these on every backend service that needs them:

- `DEBUG=false`
- `DATABASE_URL=<Render Postgres internal connection string>`
- `REDIS_CACHE_URL=<Render Key Value internal URL>/0`
- `CELERY_BROKER_URL=<Render Key Value internal URL>/1`
- `CELERY_RESULT_BACKEND=<Render Key Value internal URL>/1`
- `CHANNEL_LAYERS_REDIS_URL=<Render Key Value internal URL>/2`
- `ALLOWED_ORIGINS=https://soccho-frontend.onrender.com,https://soccho-gateway.onrender.com`
- `AXES_ENABLED=false`

And the service secrets:

- `AUTH_SECRET_KEY`
- `SOCIAL_SECRET_KEY`
- `TRANSACTION_SECRET_KEY`
- `NOTIFICATION_SECRET_KEY`
- `ADMIN_SECRET_KEY`
- `GATEWAY_SECRET_KEY`
- `AES_SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `ADMIN_URL_PATH`

## 7. Current deployment verdict

After the wiring fixes in this repo:

- HTTP proxy env wiring is now configurable for Render.
- `DATABASE_URL` fallback is now supported in the Django services.
- frontend auth/session wiring is improved.
- notification resolve flow no longer depends on a missing transaction gRPC method.

But this project is **not** a simple 4-service Render deploy.

It is only realistically deployable on Render if you use the split layout above, because:

- the gateway needs private HTTP services
- cross-service communication still depends on separate gRPC listeners
- notifications use a public WebSocket endpoint
- transaction reminders need a Celery worker

## 8. Recommended deployment order

1. Create Render Postgres
2. Create Render Key Value
3. Deploy private gRPC services
4. Deploy private HTTP services
5. Deploy transaction worker
6. Deploy public notification service
7. Deploy public gateway
8. Deploy public admin
9. Deploy frontend static site

## 9. Quick sanity checklist

- Gateway `/health` returns `200`
- Frontend can log in through gateway
- `VITE_NOTIFICATION_WS_URL` points to the public notification service
- Gateway can reach all private HTTP and gRPC services through internal networking
- Notification service can call transaction resolve endpoint through `TRANSACTION_HTTP_BASE_URL`
- Celery worker is running and connected to Redis
