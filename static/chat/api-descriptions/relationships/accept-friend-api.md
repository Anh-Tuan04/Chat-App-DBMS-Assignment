# Friend Requests API

## Accept Friend Request

Accept a pending friend request received by the logged-in user. The user is identified by the session cookie, and the request is identified by `request_id` in the query string, so the request has no body.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/friend-requests/accept?request_id={request_id}` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `request_id` | integer | Yes | A pending request addressed to the logged-in user | ID of the request to accept, taken from Get Friend Requests |

**Example**

```
POST /api/friend-requests/accept?request_id=15
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

#### 200 OK — Request accepted

```json
{
  "friend_id": 7
}
```

| Field | Type | Description |
|-------|------|-------------|
| `friend_id` | integer | ID of the user who is now a friend (the one who sent the request). Lets the client confirm which request was accepted |

After accepting, the two users are friends and the request no longer appears in Get Friend Requests.

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
| `400` | `request_id` is missing or not an integer | `"request_id is required"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `404` | No pending request with this ID, or it is not addressed to the logged-in user (including already accepted or declined) | `"Friend request not found"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 404**

```json
{
  "message": "Friend request not found"
}
```