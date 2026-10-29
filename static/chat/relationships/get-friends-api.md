# Friends API

## Get Friend List

Get all friends of the logged-in user. The user is identified by the session cookie, so no user ID is passed.

### Endpoint

| Method | URL |
|--------|-----|
| `GET` | `{BASE_URL}/api/friends` |

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

The body is an array, sorted by friend's display name. It is `[]` if the user has no friends.

```json
[
  {
    "friend_id": 7,
    "friend_username": "jane_doe",
    "friend_display_name": "Jane Doe",
    "friend_avatar_url": "https://example.com/avatars/jane.png",
    "friend_online_status": "online"
  },
  {
    "friend_id": 21,
    "friend_username": "mike99",
    "friend_display_name": "Mike",
    "friend_avatar_url": null,
    "friend_online_status": "offline"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `friend_id` | integer | Friend's user ID |
| `friend_username` | string | Friend's username |
| `friend_display_name` | string | Friend's display name |
| `friend_avatar_url` | string \| null | Friend's avatar URL, null if not set |
| `friend_online_status` | string | `online`, `idle`, `offline` or `do_not_disturb` |

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