# Conversations API

## Create Conversation

Start a new direct conversation between the logged-in user and another user. A conversation can only be created together with its first message, so the message must not be empty. The sender is identified by the session cookie, and the other user is identified by `user_id` in the query string.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/conversations/new-conversation?user_id={user_id}` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `user_id` | integer | Yes | Existing user, not the logged-in user | ID of the user to start the conversation with |

**Example**

```
POST /api/conversations/new-conversation?user_id=7
```

### Request

**Headers**

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Content-Type` | `application/json` | Yes | Body format |
| `Cookie` | `session=<session_id>` | Yes | Session started by Login. Sent automatically by the browser. With `fetch`, use `credentials: "include"` for cross-origin calls |
| `Accept` | `application/json` | No | Response format |

**Body**

```json
{
  "message": "string"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `message` | string | Yes | 1–2000 chars, not empty and not only whitespace | First message of the conversation |

**Example**

```json
{
  "message": "Hi Jane, how are you?"
}
```

### Response

**Headers**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

#### 201 Created — Conversation created

The body has the same fields as one element of the Get Conversation List response, so the client can add it straight into its conversation list.

```json
{
  "conversation_id": 3,
  "conversation_type": "direct",
  "receiver_id": 7,
  "receiver_display_name": "Jane Doe",
  "conversation_img_url": "https://example.com/avatars/jane.png"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | integer | ID of the new conversation. Also the ID used to load and send messages |
| `conversation_type` | string | Always `direct` for this endpoint |
| `receiver_id` | integer | ID of the user the conversation was started with. Lets the client confirm it went to the intended user |
| `receiver_display_name` | string | The other user's display name |
| `conversation_img_url` | string \| null | The other user's avatar URL, null if not set |

The first message is saved as part of the same request.

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
| `400` | `user_id` is missing, not an integer, or is the logged-in user; or `message` is missing, empty, only whitespace, or too long | `"Message must not be empty"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `404` | Target user does not exist, or a block exists between the two users | `"User not found"` |
| `409` | A direct conversation between the two users already exists | `"Conversation already exists"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 400**

```json
{
  "message": "Message must not be empty"
}
```