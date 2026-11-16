
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
 
The array is sorted by most recent activity: conversations are ordered by `latest_message.created_at`, newest first. A conversation whose `latest_message` is `null` comes after those with a message, ordered by creation time.
 
```json
[
  {
    "conversation_id": 1,
    "conversation_type": "direct",
    "receiver_id": 7,
    "display_name": "Jane Doe",
    "conversation_img_url": "https://example.com/avatars/jane.png",
    "latest_message": {
      "message_id": "5f1c2a9e-8b7d-11ef-9c3a-0242ac120002",
      "sender_id": 7,
      "sender_display_name": "Jane Doe",
      "message_type": "text",
      "content": "See you tomorrow!",
      "created_at": "2026-11-16T14:20:00Z"
    }
  },
  {
    "conversation_id": 2,
    "conversation_type": "group",
    "receiver_id": null,
    "display_name": "Project Team",
    "conversation_img_url": null,
    "latest_message": null
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
| `latest_message` | object \| null | Most recent message in the conversation. `null` if the conversation has no messages yet (for example a new group) |
 
**`latest_message` fields** (place null now. Will implement later)
 
Present only when `latest_message` is not `null`. These fields are the same as one item of the Get Messages response, so the client can use one message renderer for both.
 
| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Message ID (Cassandra time-based UUID) |
| `sender_id` | integer | ID of the user who sent the message. Compare with the logged-in user to show "You: ..." |
| `sender_display_name` | string | Display name of the sender. Useful for group previews such as "Jane: See you tomorrow!" |
| `message_type` | string | Always `text` for now. Reserved for future types such as `image` or `file` |
| `content` | string | Message text |
| `created_at` | string | Time the message was sent, ISO 8601 UTC |
 
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