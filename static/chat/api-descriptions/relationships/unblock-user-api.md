## Unblock User
 
Remove a block the logged-in user set on another user. The logged-in user is identified by the session cookie, and the user to unblock is identified by `user_id` in the query string, so the request has no body.
 
Unblocking has these effects:
- The friendship and friend requests that were removed when the user was blocked are not restored. The two users have to send a new friend request to become friends again.
- The two users can find each other in Search Users again, and can send friend requests and start conversations with each other.
### Endpoint
 
| Method | URL |
|--------|-----|
| `DELETE` | `{BASE_URL}/api/blocks?user_id={user_id}` |
 
### Path Params
 
None.
 
### Query Params
 
| Param | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `user_id` | integer | Yes | A user the logged-in user has blocked | ID of the user to unblock |
 
**Example**
 
```
DELETE /api/blocks?user_id=7
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
 
#### 200 OK — User unblocked
 
```json
{
  "unblocked_id": 7
}
```
 
| Field | Type | Description |
|-------|------|-------------|
| `unblocked_id` | integer | ID of the user who is no longer blocked. Lets the client confirm the right user was unblocked |
 
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
| `404` | The logged-in user has not blocked this user (or the user does not exist) | `"Block not found"` |
| `500` | Unexpected server error | `"Internal server error"` |
 
**Example — 404**
 
```json
{
  "message": "Block not found"
}
```