# Blocks API

## Block User

Block another user. The logged-in user is identified by the session cookie, and the user to block is identified by `user_id` in the query string, so the request has no body.

Blocking has these effects:
- If the two users are friends, the friendship is removed.
- Pending friend requests between the two users, in either direction, are removed.
- Existing conversations and messages between them are not deleted.
- The blocked user is not told about the block. They can no longer find the blocker in Search Users, and sending a friend request or starting a conversation with the blocker fails with `404 User not found`.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/blocks?user_id={user_id}` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `user_id` | integer | Yes | Existing user, not the logged-in user | ID of the user to block |

**Example**

```
POST /api/blocks?user_id=7
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

#### 201 Created — User blocked

```json
{
  "blocked_id": 7
}
```

| Field | Type | Description |
|-------|------|-------------|
| `blocked_id` | integer | ID of the user who is now blocked. Lets the client confirm the right user was blocked |

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
| `400` | `user_id` is missing, not an integer, or is the logged-in user | `"Cannot block yourself"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `404` | The user does not exist | `"User not found"` |
| `409` | The logged-in user has already blocked this user | `"User is already blocked"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 409**

```json
{
  "message": "User is already blocked"
}
```