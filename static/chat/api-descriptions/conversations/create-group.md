# Conversations API

## Create Group

Create a new group conversation. The logged-in user becomes the owner of the group, and the users in `member_ids` become members. The creator is identified by the session cookie, so the creator's ID is not sent.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/conversations/new-group` |

Example base URL: `http://localhost:5000`

### Path Params

None.

### Query Params

None.

### Request

**Headers**

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Content-Type` | `application/json` | Yes | Body format |
| `Cookie` | `user_id=<user_id>` | Yes | Session started by Login. Sent automatically by the browser. With `fetch`, use `credentials: "include"` for cross-origin calls |
| `Accept` | `application/json` | No | Response format |

**Body**

```json
{
  "group_name": "string",
  "member_ids": [0]
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `group_name` | string | Yes | 1–100 chars after trimming, not empty or only whitespace | Name of the group |
| `member_ids` | array of integer | Yes | 1–99 existing users, no duplicates, must not contain the logged-in user | IDs of the users to add to the group |

**Example**

```json
{
  "group_name": "Project Team",
  "member_ids": [7, 12, 21]
}
```

### Response

**Headers**

| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |

#### 201 Created — Group created

The body has the same shape as one item of Get Conversation List, so the client can add it to the list directly.

```json
{
  "conversation_id": 4,
  "conversation_type": "group",
  "receiver_id": null,
  "receiver_display_name": "Project Team",
  "conversation_img_url": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | integer | New conversation ID. Also the ID used to load and send messages |
| `conversation_type` | string | Always `group` |
| `receiver_id` | null | Always `null` for a group |
| `receiver_display_name` | string | Group name |
| `conversation_img_url` | string \| null | Group image URL. `null` for a new group |

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
| `400` | `group_name` is missing, empty, whitespace only, or too long; or `member_ids` is missing, empty, too long, has duplicates, contains non-integers, or contains the logged-in user | `"Group name must not be empty"` |
| `401` | `Cookie` header is missing, or the session is invalid or expired | `"Not logged in"` |
| `404` | One or more users in `member_ids` do not exist, or a block exists between the logged-in user and one of them | `"User not found"` |
| `500` | Unexpected server error | `"Internal server error"` |

**Example — 400**

```json
{
  "message": "Group name must not be empty"
}
```