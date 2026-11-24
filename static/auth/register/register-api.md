# Auth API

## Register

Create a new user account.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/auth/register` |

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
  "display_name": "string",
  "username": "string",
  "password": "string"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `display_name` | string | Yes | 1–50 chars | Name shown to other users in chats |
| `username` | string | Yes | 3–50 chars, letters/digits/underscore, unique | Login name |
| `password` | string | Yes | 6–128 chars | Account password (plain text over HTTPS) |

**Example**

```json
{
  "display_name": "John Doe",
  "username": "john_doe",
  "password": "secret123"
}
```

### Response

**Headers**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

#### 201 Created — Register success

```json
{
  "user_id": 1,
  "username": "string",
  "display_name": "string",
  "created_at": "2026-10-29T08:31:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | integer | New user ID |
| `username` | string | Username |
| `display_name` | string | Display name |
| `created_at` | string | Creation time, ISO 8601 UTC |

The password is never returned. The client should call the Login endpoint next to get a token.

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
| `400` | Missing field, wrong type, or constraint violated | `"Password must be at least 6 characters"` |
| `409` | A user with this username already exists | `"Username is already in use"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 409**

```json
{
  "message": "Username is already in use"
}
```