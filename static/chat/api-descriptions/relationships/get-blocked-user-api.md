## Get Blocked Users

Get the users the logged-in user has blocked, loaded in pages. The first request returns the most recently blocked users. To load the next page, send the `block_id` of the last item already loaded as `before`. The logged-in user is identified by the session cookie, so no user ID is passed.

Only blocks set **by** the logged-in user are listed. Users who blocked the logged-in user are never shown.

### Endpoint

| Method | URL |
|--------|-----|
| `GET` | `{BASE_URL}/api/blocks?limit={limit}&before={block_id}` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `limit` | integer | No | 1–100, default `50` | Maximum number of blocked users to return |
| `before` | integer | No | A `block_id` from an earlier page | Return only blocks older than this one. If omitted, the newest blocks are returned |

**Examples**

First page:

```
GET /api/blocks
```

Next page:

```
GET /api/blocks?limit=50&before=12
```

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

The body is an array, most recently blocked first. It is `[]` if the user has not blocked anyone (or there are no older blocks than `before`).

```json
[
  {
    "block_id": 15,
    "blocked_id": 7,
    "blocked_username": "jane_doe",
    "blocked_display_name": "Jane Doe",
    "blocked_avatar_url": null,
    "created_at": "2026-11-20T09:15:00Z"
  },
  {
    "block_id": 12,
    "blocked_id": 21,
    "blocked_username": "mike99",
    "blocked_display_name": "mike99",
    "blocked_avatar_url": null,
    "created_at": "2026-11-18T17:42:00Z"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `block_id` | integer | ID of the block. Use the last item's `block_id` as `before` to load the next page |
| `blocked_id` | integer | ID of the blocked user. Pass it as `user_id` to Unblock User |
| `blocked_username` | string | Blocked user's username |
| `blocked_display_name` | string | Blocked user's display name. Same as `blocked_username` if the user has no display name |
| `blocked_avatar_url` | string \| null | Blocked user's avatar URL, null if not set |
| `created_at` | string | Time the user was blocked, ISO 8601 UTC |

There is no "has more" field. If the array has fewer items than `limit`, there are no older blocks left.

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
| `400` | `limit` is not from 1 to 100, or `before` is not an integer | `"limit must be between 1 and 100"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 400**

```json
{
  "message": "limit must be between 1 and 100"
}
```
