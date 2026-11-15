# Search Users API

## Search Users

Look up users by a search string. The server does the pattern matching, and the client only sends the raw text. The logged-in user is identified by the session cookie.

### Endpoint

| Method | URL |
|--------|-----|
| `GET` | `{BASE_URL}/api/users/search?username={keyword}` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `username` | string | Yes | 1–50 chars, URL-encoded | Search string. The server matches it against usernames (pattern matching) |

**Example**

```
GET /api/users/search?q=john
```

### Request

**Headers**

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Cookie` | `session=<session_id>` | Yes | |
| `Accept` | `application/json` | No | Response format |

**Body**

None.

### Response

**Headers**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

#### 200 OK — Success

The body is an array. It is `[]` if nothing matches.

```json
[
  {
    "user_id": 7,
    "username": "john_doe",
    "display_name": "John Doe",
    "avatar_url": "https://example.com/avatars/john.png"
  },
  {
    "user_id": 12,
    "username": "johnny",
    "display_name": "Johnny Smith",
    "avatar_url": null
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | integer | User ID |
| `username` | string | Username |
| `display_name` | string | Display name |
| `avatar_url` | string \| null | Avatar URL, null if not set |

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
| `400` | `username` is missing, empty, or longer than 50 chars | `"Search keyword is required"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 400**

```json
{
  "message": "Search keyword is required"
}
```