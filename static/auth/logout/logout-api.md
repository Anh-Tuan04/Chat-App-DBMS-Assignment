# Auth API

## Logout

End the current session. The session is identified by the cookie header, so the request has no body.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/auth/logout` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

None.

### Request

**Headers**

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Cookie` | `session=<session_id>` | Yes | Session started by Login. Sent automatically by the browser. With `fetch`, use `credentials: "include"` for cross-origin calls |
| `Accept` | `application/json` | No | Response format |

**Body**

None.

### Response

#### 204 No Content — Logout success

**Headers**

| Header | Value | Description |
|--------|-------|-------------|
| `Set-Cookie` | `session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/` | Clears the session cookie in the browser |

**Body**

None. The session on the server is no longer valid.

#### Error Responses

The HTTP status code tells the client what kind of error it is, so the body has only one field.

**Headers**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

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
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 401**

```json
{
  "message": "Not logged in"
}
```