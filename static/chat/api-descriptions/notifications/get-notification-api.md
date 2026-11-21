# Notifications API

## Get Notifications

Get the notifications of the logged-in user (shown under the bell icon): friend requests received, friend requests accepted, and being added to a group. The logged-in user is identified by the session cookie, so no user ID is passed.

New notifications are also pushed in real time over socket.io, with the same shape as one item of this response.

### Endpoint

| Method | URL |
|--------|-----|
| `GET` | `{BASE_URL}/api/notifications?before={notification_id}&limit={limit}` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `before` | string | No | A numeric `notification_id` | Return only notifications older than this one. If omitted, the newest notifications are returned |
| `limit` | integer | No | 1–100, default `30` | Maximum number of notifications to return |

**Examples**

First page:

```
GET /api/notifications
```

Older notifications:

```
GET /api/notifications?before=1789432156738291900&limit=30
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

The body is an array, newest notification first. It is `[]` if there are no notifications (or no older ones than `before`).

```json
[
  {
    "notification_id": "1789432156738291900",
    "notification_type": "friend_request",
    "is_read": false,
    "created_at": "2026-11-19T05:20:00Z",
    "payload": {
      "actor": {
        "user_id": 7,
        "username": "jane_doe",
        "display_name": "Jane Doe",
        "avatar_url": "https://example.com/avatars/jane.png"
      }
    }
  },
  {
    "notification_id": "1789432156738291850",
    "notification_type": "friend_accepted",
    "is_read": true,
    "created_at": "2026-11-18T10:02:00Z",
    "payload": {
      "actor": {
        "user_id": 12,
        "username": "johnny",
        "display_name": "Johnny Smith",
        "avatar_url": null
      }
    }
  },
  {
    "notification_id": "1789432156738291800",
    "notification_type": "group_added",
    "is_read": false,
    "created_at": "2026-11-17T08:30:00Z",
    "payload": {
      "actor": {
        "user_id": 21,
        "username": "mike99",
        "display_name": "Mike",
        "avatar_url": null
      },
      "conversation_id": 4,
      "group_name": "Project Team"
    }
  }
]
```

**Fields of each notification**

These fields are the same for every type.

| Field | Type | Description |
|-------|------|-------------|
| `notification_id` | string | Notification ID. A 64-bit integer sent as a string so JavaScript does not lose precision. Use the last item's `notification_id` as `before` to load older notifications |
| `notification_type` | string | What happened. Decides the shape of `payload`. See the table below |
| `is_read` | bool | `true` if the user has not read this notification yet, `false` if the user has already read |
| `created_at` | string | Time the notification was created, ISO 8601 UTC |
| `payload` | object | Details of the notification. Its fields depend on `notification_type` |

**`payload` by `notification_type`**

| `notification_type` | Meaning | `payload` fields |
|---------------------|---------|------------------|
| `friend_request` | Someone sent the logged-in user a friend request | `actor` |
| `friend_accepted` | Someone accepted the logged-in user's friend request | `actor` |
| `group_added` | The logged-in user was added to a group | `actor`, `conversation_id`, `group_name` |

| `payload` field | Type | Description |
|-----------------|------|-------------|
| `actor` | object | The user who caused the notification: the sender for `friend_request`, the user who accepted for `friend_accepted`, the user who created the group or added the logged-in user for `group_added` |
| `actor.user_id` | integer | User ID. For `friend_request`, use it as `user_id` in Accept Friend Request |
| `actor.username` | string | Username |
| `actor.display_name` | string | Display name |
| `actor.avatar_url` | string \| null | Avatar URL, null if not set, but always null now |
| `conversation_id` | integer | Only for `group_added`. ID of the group conversation |
| `group_name` | string | Only for `group_added`. Name of the group |

The client should ignore a `notification_type` it does not know, so new types can be added later without breaking it.

A `friend_request` notification is returned only while the request is still pending. If it was accepted, declined, or removed (for example because of a block), it is left out of the list.

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
| `400` | `before` is not a valid notification ID, or `limit` is not an integer from 1 to 100 | `"limit must be between 1 and 100"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 401**

```json
{
  "message": "Not logged in"
}
```