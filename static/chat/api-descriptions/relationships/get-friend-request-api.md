# Friend Requests API

## Get Friend Requests

Get all pending friend requests received by the logged-in user. The user is identified by the session cookie, so no user ID is passed.

### Endpoint

| Method | URL |
|--------|-----|
| `GET` | `{BASE_URL}/api/relationships/friend-requests` |

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

**Headers**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

#### 200 OK — Success

The body is an array, newest request first. It is `[]` if there are no pending requests.

```json
[
  {
    "request_id": 15,
    "requester_id": 7,
    "requester_username": "jane_doe",
    "requester_display_name": "Jane Doe",
    "requester_avatar_url": "https://example.com/avatars/jane.png",
    "created_at": "2026-10-29T09:20:00Z"
  },
  {
    "request_id": 12,
    "requester_id": 21,
    "requester_username": "mike99",
    "requester_display_name": "Mike",
    "requester_avatar_url": null,
    "created_at": "2026-10-28T14:05:00Z"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | integer | Friend request ID. Used to accept the request |
| `requester_id` | integer | ID of the user who sent the request |
| `requester_username` | string | Sender's username |
| `requester_display_name` | string | Sender's display name |
| `requester_avatar_url` | string \| null | Sender's avatar URL, null if not set |
| `created_at` | string | Time the request was sent, ISO 8601 UTC |

Only requests with status `pending` are returned. Declined requests are not listed.

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
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 401**

```json
{
  "message": "Not logged in"
}
```