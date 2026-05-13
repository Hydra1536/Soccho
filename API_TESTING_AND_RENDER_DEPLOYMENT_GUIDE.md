# Soccho API Testing Playbook (Copy/Paste Ready)

Use this file as an executable checklist.
Replace placeholders like `<GATEWAY_URL>`, `<ACCESS_TOKEN>`, `<UUID>`.

## 0) Base Setup

```bash
# PowerShell examples use these env vars first
$env:GATEWAY_URL = "http://localhost:8000"
# Render example:
# $env:GATEWAY_URL = "https://soccho-gateway.onrender.com"
```

Headers used often:
- `Authorization: Bearer <ACCESS_TOKEN>`
- `Content-Type: application/json`
- `X-Service: transaction` (for GraphQL routed via Gateway)

---

## 1) Gateway Health

### Request
```bash
curl "$env:GATEWAY_URL/health"
```

### Expected Response (200)
```json
{"status":"ok"}
```

---

## 2) Auth Service (via Gateway)

## 2.1 Register
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user_01",
    "email": "test01@example.com",
    "password": "StrongPass123!",
    "confirm_password": "StrongPass123!"
  }'
```

### Expected Response (200)
```json
{"message":"OTP sent successfully"}
```

---

## 2.2 Verify OTP (register context)
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/auth/otp/verify/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user_01",
    "code": "123456",
    "context": "register"
  }'
```

### Expected Response (200)
```json
{
  "access": "<jwt_access>",
  "refresh": "<jwt_refresh>"
}
```

---

## 2.3 Login
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user_01",
    "password": "StrongPass123!"
  }'
```

### Expected Response (200)
```json
{
  "access": "<jwt_access>",
  "refresh": "<jwt_refresh>"
}
```

---

## 2.4 Refresh Token Rotation
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/auth/refresh/" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<OLD_REFRESH_TOKEN>"}'
```

### Expected Response (200)
```json
{
  "access": "<new_access>",
  "refresh": "<new_refresh>"
}
```

### Rotation validation
- Reusing `OLD_REFRESH_TOKEN` again should fail (401).

Expected failure body:
```json
{"detail":"Invalid credentials"}
```

---

## 2.5 Forgot Password (send OTP)
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/auth/forgot-password/" \
  -H "Content-Type: application/json" \
  -d '{"email":"test01@example.com"}'
```

### Expected Response (200)
```json
{"message":"OTP sent successfully"}
```

---

## 2.6 Verify OTP (forgot context)
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/auth/otp/verify/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user_01",
    "code": "123456",
    "context": "forgot"
  }'
```

### Expected Response (200)
```json
{
  "access": "<jwt_access>",
  "refresh": "<jwt_refresh>"
}
```

---

## 2.7 Change Password Request
### Request (use your actual backend path if different)
```bash
curl -X POST "$env:GATEWAY_URL/api/auth/change-password/request/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user_01",
    "old_password": "StrongPass123!",
    "new_password": "NewStrongPass123!",
    "confirm_password": "NewStrongPass123!"
  }'
```

### Expected Response (200)
```json
{"message":"Password changed successfully"}
```

If your backend uses `/api/auth/change-password/`, call that path instead.

---

## 2.8 Logout
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/auth/logout/" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<REFRESH_TOKEN>"}'
```

### Expected Response
- `204 No Content`

---

## 2.9 Standard auth failure body (all auth errors)
### Expected
```json
{"detail":"Invalid credentials"}
```

---

## 3) Social Service (via Gateway)

## 3.1 Send Friend Request
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/social/send-request/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<FRIEND_USER_UUID>"}'
```

### Expected Response (201)
```json
{
  "id": 1,
  "requester_id": "<uuid>",
  "addressee_id": "<uuid>",
  "status": "pending",
  "created_at": "<iso>",
  "updated_at": "<iso>"
}
```

---

## 3.2 Accept Friend Request
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/social/accept/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<REQUESTER_UUID>"}'
```

### Expected Response (200)
```json
{
  "id": 1,
  "requester_id": "<uuid>",
  "addressee_id": "<uuid>",
  "status": "accepted",
  "created_at": "<iso>",
  "updated_at": "<iso>"
}
```

---

## 3.3 Reject Friend Request
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/social/reject/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<REQUESTER_UUID>"}'
```

### Expected Response (200)
```json
{
  "id": 1,
  "requester_id": "<uuid>",
  "addressee_id": "<uuid>",
  "status": "rejected",
  "created_at": "<iso>",
  "updated_at": "<iso>"
}
```

---

## 3.4 List Friends (Cursor pagination)
Use your current route (`/api/social/list/` or `/api/social/friends/`).

### Request
```bash
curl "$env:GATEWAY_URL/api/social/list/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Expected Response (200)
```json
{
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "requester_id": "<uuid>",
      "addressee_id": "<uuid>",
      "status": "accepted",
      "created_at": "<iso>",
      "updated_at": "<iso>"
    }
  ]
}
```

---

## 3.5 Search Friends
### Request
```bash
curl "$env:GATEWAY_URL/api/social/search/?q=rahim" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Expected Response (200)
```json
{
  "results": [
    {"id":"<uuid>","username":"rahim"}
  ]
}
```

---

## 3.6 Search History (Redis JSON strings)
### Request
```bash
curl "$env:GATEWAY_URL/api/social/search/history/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Expected Response (200)
```json
{
  "history": [
    "{\"query\":\"rahim\",\"ts\":1715611111}",
    "{\"query\":\"fatima\",\"ts\":1715611100}"
  ]
}
```

---

## 4) Transaction Service (via Gateway)

## 4.1 Create Transaction (idempotent)
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/transactions/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "lender_id": "<LENDER_UUID>",
    "borrower_id": "<BORROWER_UUID>",
    "friendship_id": "<FRIENDSHIP_UUID>",
    "amount": 5000,
    "due_date": "2026-06-30",
    "idempotency_key": "<UUIDv4>"
  }'
```

### Expected Response (201)
```json
{
  "id": "<transaction_uuid>",
  "lender_id": "<uuid>",
  "borrower_id": "<uuid>",
  "friendship_id": "<uuid>",
  "amount": 5000,
  "due_date": "2026-06-30",
  "status": "pending",
  "idempotency_key": "<UUIDv4>"
}
```

### Duplicate idempotency key behavior
- Same payload + same key should return existing transaction or conflict per implementation.

---

## 4.2 Confirm Transaction
### Request
```bash
curl -X POST "$env:GATEWAY_URL/api/transactions/<TRANSACTION_UUID>/confirm/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "borrower_id": "<BORROWER_UUID>",
    "expected_version": 0
  }'
```

### Expected Response (200)
```json
{
  "id": "<transaction_uuid>",
  "status": "confirmed"
}
```

### Version conflict expected response (409)
```json
{"detail":"Version mismatch"}
```

---

## 5) GraphQL Through Gateway (Transaction routing)

Always include:
- `X-Service: transaction`
- `Authorization` bearer token

## 5.1 dashboardSummary
### Request
```bash
curl -X POST "$env:GATEWAY_URL/graphql/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Service: transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($userId: UUID!){ dashboardSummary(userId:$userId){ userId totalLent totalBorrowed totalConfirmed } }",
    "variables": { "userId": "<USER_UUID>" }
  }'
```

### Expected Response (200)
```json
{
  "data": {
    "dashboardSummary": {
      "userId": "<uuid>",
      "totalLent": 10000.0,
      "totalBorrowed": 4000.0,
      "totalConfirmed": 3
    }
  }
}
```

---

## 5.2 friendLedger
### Request
```bash
curl -X POST "$env:GATEWAY_URL/graphql/" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Service: transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query($friendshipId: UUID!){ friendLedger(friendshipId:$friendshipId){ friendshipId netBalance transactions { id lenderId borrowerId friendshipId amount status dueDate } } }",
    "variables": { "friendshipId": "<FRIENDSHIP_UUID>" }
  }'
```

### Expected Response (200)
```json
{
  "data": {
    "friendLedger": {
      "friendshipId": "<uuid>",
      "netBalance": 6000.0,
      "transactions": [
        {
          "id": "<tx_uuid>",
          "lenderId": "<uuid>",
          "borrowerId": "<uuid>",
          "friendshipId": "<uuid>",
          "amount": 5000.0,
          "status": "confirmed",
          "dueDate": "2026-06-30"
        }
      ]
    }
  }
}
```

---

## 6) Notification WebSocket (through Gateway)

## 6.1 Connect URL
- Local: `ws://localhost:8000/ws/notifications/?token=<ACCESS_TOKEN>`
- Render: `wss://<gateway-domain>/ws/notifications/?token=<ACCESS_TOKEN>`

## 6.2 Incoming created message sample
```json
{
  "event": "transaction.created",
  "notification": {
    "id": 10,
    "recipient_id": "<uuid>",
    "type": "lend_confirmation",
    "payload": {
      "transaction_id": "<tx_uuid>",
      "amount": "5000"
    },
    "is_cleared": false,
    "created_at": "2026-05-13T12:00:00Z"
  }
}
```

## 6.3 Send Agree
```json
{
  "action": "agree",
  "notification_id": "10"
}
```

## 6.4 Send Disagree
```json
{
  "action": "disagree",
  "notification_id": "10"
}
```

## 6.5 Expected WS error on downstream outage
```json
{"error":"Service Unavailable"}
```

---

## 7) Admin Service Security Checks

## 7.1 Standard /admin blocked
### Request
```bash
curl -i "<ADMIN_BASE_URL>/admin/"
```

### Expected
- `404 Not Found`

## 7.2 Obscured admin path
### Request
```bash
curl -i "<ADMIN_BASE_URL>/119115131318115/"
```

### Expected
- `200` (or `302` to login)

---

## 8) Common Failure Responses

Auth/security errors (expected everywhere in auth flow):
```json
{"detail":"Invalid credentials"}
```

Forbidden actions example:
```json
{"detail":"Forbidden"}
```

Not found example:
```json
{"detail":"Not found"}
```

---

## 9) Render Endpoint Writing Rules

Frontend must call only Gateway public URL:
- `VITE_API_URL=https://<gateway>.onrender.com`

Then frontend endpoints become:
- Auth: `https://<gateway>/api/auth/...`
- Social: `https://<gateway>/api/social/...`
- Transactions: `https://<gateway>/api/transactions/...`
- GraphQL: `https://<gateway>/graphql/` + `X-Service: transaction`
- WebSocket: `wss://<gateway>/ws/notifications/?token=<jwt>`

No frontend code rewrite needed if `VITE_API_URL` is correct.

---

## 10) Minimal End-to-End Smoke Flow

1. Register -> receive OTP
2. Verify OTP (register)
3. Login -> store tokens
4. Send friend request
5. Accept friend request (other user)
6. Create transaction (new idempotency key)
7. Confirm transaction
8. Query dashboardSummary
9. Open websocket and verify notification push

If all 9 pass, your core pipeline is healthy.
