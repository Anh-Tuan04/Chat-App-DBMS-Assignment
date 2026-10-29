# Auth API

## Login

Authenticate a user with credentials and start a session. The session is carried in a cookie header, not in the body.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/auth/login` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

None.

### Request

**Headers**

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Content-Type` | `application/json` | Yes | Body format |
| `Accept` | `application/json` | No | Response format |

**Body**

```json
{
  "username": "string",
  "password": "string"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `username` | string | Yes | 3–50 chars | Login name |
| `password` | string | Yes | 6–128 chars | Account password (plain text over HTTPS) |

**Example**

```json
{
  "username": "john_doe",
  "password": "secret123"
}
```

### Response

**Headers**

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Body format |
| `Set-Cookie` | `session=<session_id>; HttpOnly; Path=/; SameSite=Lax` | Session cookie, only on `200`. The browser stores it automatically |

#### 200 OK — Login success

```json
{
  "user_id": 1,
  "username": "string",
  "display_name": "string",
  "avatar_url": "string | null"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | integer | User ID |
| `username` | string | Username |
| `display_name` | string | Display name |
| `avatar_url` | string \| null | Avatar URL, null if not set |

The body has no token. Authentication for later requests uses the session cookie:

| Header (on later requests) | Value | Description |
|----------------------------|-------|-------------|
| `Cookie` | `session=<session_id>` | 
<!-- Sent automatically by the browser. With `fetch`, use `credentials: "include"` for cross-origin calls --> |

#### Error Responses

The HTTP status code tells the client what kind of error it is, so the body has only one field.

```json
{
  "message": "string"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Human-readable reason, safe to show to the user |

| Status | When | Example `message` |
|--------|------|-------------------|
| `400` | Missing field, wrong type, or constraint violated | `"Username is required"` |
| `401` | Username not found or password incorrect | `"Username or password is incorrect"` |
| `500` | Unexpected server error | `"Internal server error"` |

No `Set-Cookie` header is sent on errors.

**Example — 401**

```json
{
  "message": "Username or password is incorrect"
}
```