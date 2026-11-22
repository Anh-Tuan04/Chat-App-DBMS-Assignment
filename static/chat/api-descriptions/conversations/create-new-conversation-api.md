# Conversations API

## Create a Direct Conversation

Create a new direct conversation between the logged-in user and another user.
The first message is created in the same request and cannot be empty.
The logged-in user is identified by the Flask session cookie.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/conversations/new-conversation?user_id={user_id}` |

Example base URL: `http://127.0.0.1:5000`

### Query Parameters

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `user_id` | integer | Yes | Must identify an existing user other than the logged-in user | User to start the conversation with |

Example:

```http
POST /api/conversations/new-conversation?user_id=7
```

### Request

#### Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Content-Type` | `application/json` | Yes | Request body format |
| `Accept` | `application/json` | No | Expected response format |
| Cookie | Flask session cookie | Yes | Created by login; use `credentials: "include"` with `fetch` when needed |

#### Body

```json
{
  "message": "Hi Jane, how are you?"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `message` | string | Yes | 1–2000 characters; not empty or whitespace-only | First message in the conversation |

JavaScript example:

```javascript
const response = await fetch(
  "/api/conversations/new-conversation?user_id=7",
  {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ message: "Hi Jane, how are you?" })
  }
);

const data = await response.json();
```

### Successful Response

#### `201 Created`

The conversation and its first message were created successfully.

```json
{
  "conversation_id": 3,
  "conversation_type": "direct",
  "receiver_id": 7,
  "receiver_display_name": "Jane Doe",
  "conversation_img_url": "https://example.com/avatars/jane.png",
  "message_info": {
    "message_id": "123456789",
    "sender_id": 1,
    "sender_display_name": "John Doe",
    "message_type": "text",
    "content": "Hi Jane, how are you?",
    "created_at": "2026-11-22T18:05:05Z"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | integer | New conversation ID; use it to load and send messages |
| `conversation_type` | string | Always `direct` for this endpoint |
| `receiver_id` | integer | ID of the other participant |
| `receiver_display_name` | string | Display name of the other participant |
| `conversation_img_url` | string \| null | Other participant's avatar URL, or `null` |
| `message_info` | object | The first message created with the conversation |

`message_info` contains `message_id`, `sender_id`, `sender_display_name`,
`message_type`, `content`, and `created_at`. The timestamp is an ISO 8601 UTC
string.

### Error Responses

All errors use this JSON shape:

```json
{
  "message": "error description"
}
```

| Status | Condition | Example `message` |
|--------|-----------|-------------------|
| `400` | Missing or invalid `user_id`, self-conversation, invalid JSON body, empty message, or message longer than 2000 characters | `"message must not be empty"` |
| `401` | No valid login session | `"401 Unauthorized"` |
| `404` | Target user does not exist or is blocked | `"User not found"` |
| `409` | A direct conversation between the users already exists | `"Conversation already exists"` |
| `500` | Unexpected server error | `"Internal server error"` |

Example:

```json
{
  "message": "Conversation already exists"
}
```