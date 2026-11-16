# Friends API

## Unfriend

End the friendship between the logged-in user and one of their friends. The logged-in user is identified by the session cookie, and the friend is identified by `user_id` in the query string, so the request has no body.

### Endpoint

| Method | URL |
|--------|-----|
| `DELETE` | `{BASE_URL}/api/friends?user_id={user_id}` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `user_id` | integer | Yes | A current friend of the logged-in user | ID of the friend to remove (`friend_id` from Get Friend List) |

**Example**

```
DELETE /api/friends?user_id=7
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

#### 200 OK — Friend removed

```json
{
  "friend_id": 7
}
```

| Field | Type | Description |
|-------|------|-------------|
| `friend_id` | integer | ID of the user who is no longer a friend. Lets the client confirm the right friend was removed |

After removal, the user no longer appears in Get Friend List, and either user can send a new friend request to the other. Existing conversations and messages between the two users are not deleted.

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
| `400` | `user_id` is missing, not an integer, or is the logged-in user | `"user_id is required"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `404` | The user does not exist, or is not a friend of the logged-in user | `"Friend not found"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 404**

```json
{
  "message": "Friend not found"
}
```