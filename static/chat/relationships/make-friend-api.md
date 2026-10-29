# Friend API

## Send Friend Request

Send a friend request from the logged-in user to another user. The requester is identified by the session cookie, and the target user is identified by `user_id` in the query string, so the request has no body.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/relationships/friend-requests?user_id={user_id}` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `user_id` | integer | Yes | Existing user, not the logged-in user | ID of the user who will receive the request |

**Example**

```
POST /api/friend-requests?user_id=7
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

#### 201 Created — Request sent

```json
{
  "receiver_id": 7
}
```

| Field | Type | Description |
|-------|------|-------------|
| `receiver_id` | integer | ID of the user who received the request. Lets the client confirm the request went to the intended user |

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
| `400` | `user_id` is missing, not an integer, or is the logged-in user | `"Cannot send a friend request to yourself"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `404` | Target user does not exist, or a block exists between the two users | `"User not found"` |
| `409` | The two users are already friends, or a pending request already exists | `"Friend request already exists"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 409**

```json
{
  "message": "Friend request already exists"
}
```