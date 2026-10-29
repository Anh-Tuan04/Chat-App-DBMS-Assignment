# Conversations API

## Get Conversation List

Get all conversations (direct and group) of the logged-in user. The user is identified by the session cookie, so no user ID is passed.

### Endpoint

| Method | URL |
|--------|-----|
| `GET` | `{BASE_URL}/api/conversations` |

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

The body is an array. It is `[]` if the user has no conversations.

```json
[
  {
    "conversation_id": 1,
    "conversation_type": "direct",
    "receiver_id": 7,
    "display_name": "Jane Doe",
    "conversation_img_url": "https://example.com/avatars/jane.png"
  },
  {
    "conversation_id": 2,
    "conversation_type": "group",
    "receiver_id": null,
    "display_name": "Project Team",
    "conversation_img_url": null
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | integer | Conversation ID. Also the ID used to load messages |
| `conversation_type` | string | `direct` or `group` |
| `receiver_id` | integer \| null | The other user's ID for `direct`. `null` for `group` |
| `display_name` | string | Other user's display name for `direct`. Channel name for `group` |
| `conversation_img_url` | string \| null | Other user's avatar URL for `direct`. Channel image URL for `group`. `null` if not set |

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