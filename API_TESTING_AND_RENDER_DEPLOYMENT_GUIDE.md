# Soccho Production API Testing Guide (Render)

This guide is copy-paste ready for production testing on **Friday, May 15, 2026**.

## Production URLs

- Frontend (Render): `https://soccho.onrender.com`
- Frontend (Vercel): `https://soccho.vercel.app`
- Gateway: `https://soccho-gateway.onrender.com`
- Auth (direct): `https://soccho-auth.onrender.com`
- Social (direct): `https://soccho-social.onrender.com`
- Transaction (direct): `https://soccho-transaction.onrender.com`
- Notification WS: `wss://soccho-notification.onrender.com`

## Quick Setup

### PowerShell

```powershell
$env:GATEWAY_URL = "https://soccho-gateway.onrender.com"
$env:AUTH_URL = "https://soccho-auth.onrender.com"
$env:SOCIAL_URL = "https://soccho-social.onrender.com"
$env:TRANSACTION_URL = "https://soccho-transaction.onrender.com"
$env:WS_URL = "wss://soccho-notification.onrender.com"
```

### Bash

```bash
export GATEWAY_URL="https://soccho-gateway.onrender.com"
export AUTH_URL="https://soccho-auth.onrender.com"
export SOCIAL_URL="https://soccho-social.onrender.com"
export TRANSACTION_URL="https://soccho-transaction.onrender.com"
export WS_URL="wss://soccho-notification.onrender.com"
```

## 1) Health Checks

```bash
curl "$GATEWAY_URL/health"
curl "$SOCIAL_URL/health/"
curl "$TRANSACTION_URL/health/"
```

Expected:

- `200 OK`
- JSON like `{"status":"ok"}`

## 2) Auth Flow (Email + Password)

Important: login is now **email + password** (not username).

### 2.1 Register

```bash
curl -X POST "$GATEWAY_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user_01",
    "email": "test01@example.com",
    "password": "Passw0rd!234",
    "confirm_password": "Passw0rd!234"
  }'
```

Expected:

- `200 OK`
- `{"message":"OTP sent successfully"}`

### 2.2 Verify OTP (register)

```bash
curl -X POST "$GATEWAY_URL/api/auth/otp/verify/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test01@example.com",
    "code": "123456",
    "context": "register"
  }'
```

Expected:

- `200 OK`
- `{"access":"<jwt>","refresh":"<jwt>"}`

### 2.3 Login (email + password)

```bash
curl -X POST "$GATEWAY_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test01@example.com",
    "password": "Passw0rd!234"
  }'
```

Expected:

- `200 OK`
- `{"access":"<jwt>","refresh":"<jwt>"}`

### 2.4 Refresh

```bash
curl -X POST "$GATEWAY_URL/api/auth/refresh/" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<REFRESH_TOKEN>"}'
```

Expected:

- `200 OK`
- New token pair JSON

### 2.5 Forgot Password (request OTP)

```bash
curl -X POST "$GATEWAY_URL/api/auth/forgot-password/" \
  -H "Content-Type: application/json" \
  -d '{"email":"test01@example.com"}'
```

Expected:

- `200 OK`
- `{"message":"OTP sent successfully"}`

### 2.6 Change Password Request (email + old/new password)

```bash
curl -X POST "$GATEWAY_URL/api/auth/change-password/request/" \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test01@example.com",
    "old_password":"Passw0rd!234",
    "new_password":"N3wPassw0rd!456",
    "confirm_password":"N3wPassw0rd!456"
  }'
```

Expected:

- `200 OK`
- `{"message":"Password changed successfully"}`

### 2.7 Verify OTP (forgot or change password)

```bash
curl -X POST "$GATEWAY_URL/api/auth/otp/verify/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test01@example.com",
    "code": "123456",
    "context": "forgot"
  }'
```

Expected:

- `200 OK`
- `{"access":"<jwt>","refresh":"<jwt>"}`

### 2.8 Logout

```bash
curl -X POST "$GATEWAY_URL/api/auth/logout/" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<REFRESH_TOKEN>"}'
```

Expected:

- `204 No Content`

## 3) Social APIs

Use a valid access token:

```bash
export ACCESS_TOKEN="<ACCESS_TOKEN>"
```

### 3.1 Send Friend Request

```bash
curl -X POST "$GATEWAY_URL/api/social/send-request/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"11111111-1111-1111-1111-111111111111"}'
```

Expected:

- `201 Created`
- Friendship object with `status: "pending"`

### 3.2 Accept Friend Request

```bash
curl -X POST "$GATEWAY_URL/api/social/accept/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"11111111-1111-1111-1111-111111111111"}'
```

Expected:

- `200 OK`
- Friendship object with `status: "accepted"`

### 3.3 Reject Friend Request

```bash
curl -X POST "$GATEWAY_URL/api/social/reject/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"11111111-1111-1111-1111-111111111111"}'
```

Expected:

- `200 OK`
- Friendship object with `status: "rejected"`

### 3.4 List Friends

```bash
curl "$GATEWAY_URL/api/social/list/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Expected:

- `200 OK`
- DRF paginated response with `results`

### 3.5 Search Users

```bash
curl "$GATEWAY_URL/api/social/search/?q=rahim" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Expected:

- `200 OK`
- `{"results":[{"id":"<uuid>","username":"rahim","loyalty_score":<number>}...]}`

### 3.6 Search History

```bash
curl "$GATEWAY_URL/api/social/search/history/" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Expected:

- `200 OK`
- `{"history":[...]} `

## 4) Transactions APIs

### 4.1 Create Transaction

```bash
curl -X POST "$GATEWAY_URL/api/transactions/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lender_id":"22222222-2222-2222-2222-222222222222",
    "borrower_id":"33333333-3333-3333-3333-333333333333",
    "friendship_id":"44444444-4444-4444-4444-444444444444",
    "amount":"1500.00",
    "due_date":"2026-12-31",
    "idempotency_key":"txn-001"
  }'
```

Expected:

- `201 Created` on first request
- `200 OK` on safe retry with same `idempotency_key`
- Transaction object with `status: "pending"`

### 4.2 Confirm Transaction

```bash
curl -X POST "$GATEWAY_URL/api/transactions/<TRANSACTION_ID>/confirm/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "borrower_id":"33333333-3333-3333-3333-333333333333",
    "expected_version":1
  }'
```

Expected:

- `200 OK` and `status: "confirmed"`
- `404` if ID not found
- `409` if already processed or version mismatch

### 4.3 Resolve Transaction (notification action)

```bash
curl -X POST "$GATEWAY_URL/api/transactions/<TRANSACTION_ID>/resolve/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "borrower_id":"33333333-3333-3333-3333-333333333333",
    "action":"agree"
  }'
```

Expected:

- `200 OK`
- `action=agree` results in `status: "confirmed"`
- `action=disagree` results in `status: "denied"`

## 5) GraphQL via Gateway

### 5.1 Social GraphQL Friend List

```bash
curl -X POST "$GATEWAY_URL/graphql/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Service: social" \
  -d '{"query":"query FriendList { friendList { userId username loyaltyScore } }"}'
```

Expected:

- `200 OK`
- `{"data":{"friendList":[...]}}`

### 5.2 Transaction GraphQL Example

```bash
curl -X POST "$GATEWAY_URL/graphql/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Service: transaction" \
  -d '{"query":"{ __typename }"}'
```

Expected:

- `200 OK` if GraphQL endpoint is reachable

## 6) Notification WebSocket

Connect:

- `wss://soccho-notification.onrender.com/ws/notifications/?token=<ACCESS_TOKEN>`

Browser console quick test:

```javascript
const token = "<ACCESS_TOKEN>";
const ws = new WebSocket(`wss://soccho-notification.onrender.com/ws/notifications/?token=${encodeURIComponent(token)}`);
ws.onopen = () => console.log("connected");
ws.onmessage = (event) => console.log("message", event.data);
ws.onerror = (event) => console.error("error", event);
ws.onclose = () => console.log("closed");
```

Expected:

- Successful connection if token is valid
- Event payloads for transaction/notification events

## 7) Fast Failure Checklist

- `401 Invalid credentials`: bad/expired token or wrong login payload.
- `400` on GraphQL proxy: missing `X-Service` header.
- `404` on proxy route: wrong gateway path.
- `409` in transactions: idempotency/version/state conflict.

## 8) Required Frontend Env

```env
VITE_API_URL=https://soccho-gateway.onrender.com
VITE_NOTIFICATION_WS_URL=wss://soccho-notification.onrender.com
VITE_GOOGLE_CLIENT_ID=replace_google_client_id
```
