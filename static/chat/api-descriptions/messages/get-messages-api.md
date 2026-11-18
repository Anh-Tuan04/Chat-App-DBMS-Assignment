# Messages API

## Get Messages

Get the messages of one conversation, loaded in pages. The first request returns the newest messages. To load older messages (when the user scrolls up), send the `message_id` of the oldest message already loaded as `before`. The logged-in user is identified by the session cookie and must be a member of the conversation.

### Endpoint

| Method | URL |
|--------|-----|
| `GET` | `{BASE_URL}/api/messages?conversation_id={conversation_id}&before={message_id}&limit={limit}` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `conversation_id` | integer | Yes | A conversation the logged-in user belongs to | ID of the conversation (`conversation_id` from Get Conversation List) |
| `before` | string | No | A `message_id` of this conversation | Return only messages older than this message. If omitted, the newest messages are returned |
| `limit` | integer | No | 1–100, default `30` | Maximum number of messages to return |

**Examples**

First page:

```
GET /api/messages?conversation_id=1
```

Older messages:

```
GET /api/messages?conversation_id=1&before=5f1c2a9e-8b7d-11ef-9c3a-0242ac120002&limit=30
```

### Request

**Headers**

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Cookie` | `user_id=<user_id>` | Yes | Session started by Login. Sent automatically by the browser. With `fetch`, use `credentials: "include"` for cross-origin calls |
| `Accept` | `application/json` | No | Response format |

**Body**

None.

### Response

**Headers**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

#### 200 OK — Success

The body is an array, newest message first. It is `[]` if there are no messages (or no older messages than `before`).

```json
[
  {
    "message_id": "5f1c2a9e-8b7d-11ef-9c3a-0242ac120002",
    "sender_id": 7,
    "sender_display_name": "Jane Doe",
    "message_type": "text",
    "content": "See you tomorrow!",
    "created_at": "2026-11-16T14:20:00Z"
  },
  {
    "message_id": "4e0b19d8-8b7d-11ef-8a2b-0242ac120002",
    "sender_id": 1,
    "sender_display_name": "John Doe",
    "message_type": "text",
    "content": "Sounds good, what time?",
    "created_at": "2026-11-16T14:18:00Z"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message ID (Cassandra time-based UUID). Use the last item's `message_id` as `before` to load older messages |
| `sender_id` | integer | ID of the user who sent the message. Compare with the logged-in user to tell own messages from others |
| `sender_display_name` | string | Display name of the sender |
| `message_type` | string | Always `text` for now. Reserved for future types such as `image` or `file` |
| `content` | string | Message text |
| `created_at` | string | Time the message was sent, ISO 8601 UTC |

These fields are the same as `latest_message` in Get Conversation List.

There is no "has more" field. If the array has fewer items than `limit`, there are no older messages left.

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
| `400` | `conversation_id` is missing or not an integer; `before` is not a valid message ID; or `limit` is not an integer from 1 to 100 | `"conversation_id is required"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `404` | The conversation does not exist, or the logged-in user is not a member of it | `"Conversation not found"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 404**

```json
{
  "message": "Conversation not found"
}
```