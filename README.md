# Soccho

Soccho is a shared-trust money log for friends, roommates, travel groups, and informal lenders. It solves a very human problem: people often remember that money changed hands, but they do not always agree on when, why, or whether it was accepted. Soccho turns that vague social memory into a verifiable workflow: one person logs a claim, the other person explicitly verifies it, the system tracks due items chronologically, and reminders stay tied to real unsettled records instead of noisy totals.

## Product story

In the real world, lightweight debt tracking breaks down for three reasons:

- people can dispute whether a cash handoff or informal transfer actually happened,
- multiple overlapping dues get mixed together and reminders become inaccurate,
- mobile users lose context when the network is unstable or the app gets suspended.

Soccho addresses that by separating a transaction claim from an accepted due, applying repayment in FIFO order across active dues, and preserving cached history, profile state, balances, and notifications for offline reads.

## Architecture map

```text
React + Vite PWA
    |
    | HTTP / GraphQL / WebSocket
    v
FastAPI Gateway
    |
    |-- Auth Service (Django REST)
    |-- Social Service (Django REST + GraphQL)
    |-- Transaction Service (Django Ninja + GraphQL + Celery)
    |-- Notification Service (Django REST + Channels WebSocket)
    |
    +-- Embedded keepalive loop warms gateway + backend services

Shared infrastructure
    |
    |-- Postgres: users, friendships, transactions, due records, balances, notifications
    |-- Redis: cache, pub/sub, channel layer, Celery broker/result backend
```

### Runtime flow

- The frontend talks only to the gateway for HTTP and GraphQL, and to the notification service for live WebSocket pushes.
- The gateway validates JWTs, forwards `x-user-id` and `x-username`, and keeps Render containers warm with an internal async ping loop.
- The transaction service owns the verification workflow, due-record lifecycle, FIFO repayment allocation, and reminder scheduling.
- The notification service listens to Redis pub/sub, persists notifications, and broadcasts them live over Channels.
- The social service owns friendships, friend discovery, loyalty scoring inputs, and contextual user search.

## Services

### Frontend

- Mobile-first React app with PWA installability.
- Offline-first reads through `sw.js`, IndexedDB queueing for transaction POSTs, cached GraphQL responses, and cached REST profile/friends/notification reads.
- Notification drawer is read-only; verification actions live on profile/friend surfaces.

### Gateway

- FastAPI edge router for REST and GraphQL multiplexing.
- Local JWT validation keeps auth checks cheap.
- Built-in keepalive loop removes the old external keepalive worker dependency.

### Auth service

- Django REST service for register/login/refresh/logout/me/OTP/password flows.
- JWT issuance includes username so downstream services can generate human-readable notifications without extra cross-service round trips.

### Social service

- Django REST + GraphQL for friendships, friend lists, friend requests, and search.
- Contextual search combines trigram candidates, Levenshtein distance, and Soundex-style phonetic scoring.
- Redis cache entries are hard-evicted on friend acceptance and unfriend actions.

### Transaction service

- Django Ninja API + GraphQL ledger reads.
- Transactions now start as `pending_verification`.
- Agreement creates active due records.
- Repayments apply strictly FIFO by earliest due date, then creation timestamp.
- Celery reminder sweep sends due-soon and overdue item notifications per active due record.

### Notification service

- Django REST + Channels.
- Redis pub/sub listener persists typed notifications and broadcasts them live.
- Notifications link users into verification/profile flows instead of exposing approval buttons in the drawer.

## Technology matrix

| Technology | Where used | Why it was chosen |
|---|---|---|
| Python 3.12 | Gateway and all backend microservices | A single language across services keeps ops and hiring simpler while supporting both API and worker workloads well. |
| FastAPI | Gateway | Lightweight async request proxying, clean lifespan hooks for embedded keepalive, and strong HTTP ergonomics. |
| Django | Auth, Social, Transaction, Notification, Admin | Mature ORM, migrations, admin support, and rapid service development on a shared Postgres schema. |
| Django REST Framework | Auth, Social, Notification | Reliable class-based HTTP APIs, serializers, and auth-oriented request handling. |
| Django Ninja | Transaction service | Concise typed REST endpoints for transaction and repayment workflows. |
| Graphene-Django / GraphQL | Social and Transaction read models | Gives the frontend compact ledger/friend/dashboard reads without over-fetching. |
| Django Channels + Daphne | Notification service | Persistent WebSocket delivery for real-time notifications and session-safe live updates. |
| Celery | Transaction reminders and retention jobs | Durable background scheduling for due sweeps and cleanup tasks. |
| Redis | Cache, pub/sub, Celery broker/backend, Channels layer | One infrastructure component supports cache eviction, event fan-out, WebSocket groups, and worker coordination. |
| PostgreSQL | Shared system of record | Strong relational guarantees for users, friendships, transactions, due records, balances, and notifications. |
| `django-cryptography` | Auth, Social, Transaction | Encrypts sensitive fields such as money amounts, dates, notes, and email addresses at rest. |
| JWT / PyJWT | Gateway, Auth, Notification | Cheap stateless identity propagation between services. |
| React 18 | Frontend | Component-driven UI for a mobile app-like experience with predictable state composition. |
| Vite | Frontend | Fast local dev and optimized production bundling. |
| TypeScript | Frontend | Safer contract work across GraphQL, REST payloads, and UI state. |
| Apollo Client | Frontend GraphQL | Handles GraphQL transport, cache reads, refetching, and service-specific routing headers. |
| Axios | Frontend REST client | Simple interceptor-based token refresh and API error handling. |
| React Router | Frontend routing | Clean route transitions between login, home, profile, friend detail, and recovery flows. |
| Tailwind CSS | Frontend styling | Speeds up mobile UI iteration while preserving a consistent design vocabulary. |
| Motion | Frontend transitions | Keeps panels, drawers, and list reveals feeling app-like rather than web-fragmented. |
| Recharts | Home dashboard | Lightweight charts for trend and summary visualization. |
| Service Worker API | Frontend PWA | Enables shell caching, stale-while-revalidate data reads, and background sync hooks. |
| IndexedDB | Frontend offline queue | Stores pending transaction POSTs safely when the network is unavailable. |
| Web App Manifest | Frontend PWA | Makes the app installable on mobile and desktop. |
| Gunicorn | Django WSGI services | Production app server for sync Django services. |
| Render | Deployment target | Managed hosting for web services, background workers, Postgres, Redis, and static frontend delivery. |

## Key domain rules

- `pending_verification` logs do not change balances.
- `agree` converts a log into an active due record and updates balance state.
- `disagree` rejects the claim and notifies the original logger.
- Repayments reduce the earliest-expiring active due first.
- Reminders are generated from active due records, not raw transaction totals.
- Cache invalidation is hard-evict-and-rebuild on transaction settlement, friendship acceptance, and unfriend.

## Local development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Gateway

```bash
cd gateway
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Django services

```bash
cd auth && pip install -r requirements.txt && python manage.py migrate
cd social && pip install -r requirements.txt && python manage.py migrate
cd transaction && pip install -r requirements.txt && python manage.py migrate
cd notification && pip install -r requirements.txt && python manage.py migrate
```

### Transaction worker

```bash
cd transaction
celery -A transaction_service worker -B
```

## What changed in this repository

- Verification moved off the notification dropdown and into profile-level action surfaces.
- Active debts are now modeled explicitly as due records.
- Repayments now settle by FIFO deadline order.
- The gateway owns keepalive behavior; the standalone keepalive worker was removed.
- The frontend now ships with a real manifest, installable PWA metadata, offline caches, and queued transaction sync.
 