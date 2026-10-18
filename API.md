# Message App – HTTP API Reference

Flask server (`server.py`) for the message app. Browsers talk only to this server; it calls the MySQL and Cassandra handlers over gRPC.

- **Base URL:** `http://<server-ip>:5000` (plain HTTP, intended for a LAN or virtual LAN)
- **Last updated:** 2026-10-18

## Endpoints at a glance

| Method | Path | Login required | Purpose |
|---|---|---|---|
| `GET` | `/` | No | Login page |
| `POST` | `/login` | No | Check credentials and start a session |
| `GET` | `/app` | Yes (page) | Chat page |
| `POST` | `/messages` | Yes (API) | Send a message |
| `GET` | `/static/<filename>` | No | CSS and JavaScript files |

## Conventions

### Sessions

- A successful `POST /login` sets a cookie named `session`: `Set-Cookie: session=<signed>; HttpOnly; Path=/`.
- The cookie is signed (not encrypted) and holds only `user_id`. The browser sends it automatically on later requests.
- The signing key is the `SECRET_KEY` environment variable. If it isn't set, a random key is generated at startup, so **restarting the server invalidates every session**.
- There is no logout endpoint yet.
- Protected routes react differently when there is no valid session:
  - **Pages** (`GET /app`) answer `302` with `Location: /`.
  - **API routes** (`POST /messages`) answer `401` with an empty body.

### Requests

- JSON endpoints require the header `Content-Type: application/json`. A body that isn't valid JSON, isn't a JSON object, or is sent with another content type is treated as invalid (`400`).
- The sender of a message is never taken from the request. It is always the `user_id` in the session.

### Responses

- **The HTTP status code is the result.** There is no `status` field in any body.
- Errors produced by this app (`400`, `401`, `500`, `503`) have an **empty body**.
- Errors produced by Flask itself (`404`, `405`, `413`) are **HTML error pages**. Clients should not try to parse them as JSON.
- The only JSON the server sends is the `{"redirect": ...}` body of a successful login.

### Limits

| What | Limit | Result when exceeded |
|---|---|---|
| Request body size | 64 KB | `413` |
| `username` length | 255 characters | `400` |
| `password` length | 1024 characters | `400` |
| Message `content` length | 4000 characters | `400` |

---

## `GET /`

Returns the login page (`login.html`).

- **Auth:** none. The page is served even to a user who is already logged in.
- **Response:** `200 OK`, `text/html`.

---

## `POST /login`

Checks the credentials through `authenticate()` (which is meant to ask the MySQL handler; see [Current limitations](#current-limitations)). On success it starts a session and tells the client where to go next.

- **Auth:** none.

**Request body** (JSON)

| Field | Type | Rules |
|---|---|---|
| `username` | string | non-empty, at most 255 characters |
| `password` | string | non-empty, at most 1024 characters |

**Responses**

| Code | Meaning | Body |
|---|---|---|
| `200 OK` | Credentials accepted. The `session` cookie is set. | `{"redirect": "/app"}` |
| `400 Bad Request` | Body is missing, not a JSON object, or not sent as JSON. Or `username`/`password` is missing, empty, not a string, or too long. The MySQL handler is not contacted. | empty |
| `401 Unauthorized` | `authenticate()` returned `None`: wrong username or password. The two cases are deliberately indistinguishable. | empty |
| `413 Request Entity Too Large` | Body larger than 64 KB. | Flask HTML page |
| `503 Service Unavailable` | `authenticate()` raised `MySQLServiceUnavailable`: the MySQL handler (or its database) is unavailable. This is not a wrong-password result. | empty |

Other methods on this path return `405` (with `Allow: OPTIONS, POST`).

**Example**

```bash
curl -i -c cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}' \
  http://<server-ip>:5000/login
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Set-Cookie: session=<signed>; HttpOnly; Path=/

{"redirect":"/app"}
```

**Web client behavior (`login.js`):** `200` navigates to `redirect`. `401` shows "Sai tên người dùng hoặc mật khẩu.", `503` shows "Dịch vụ đăng nhập tạm thời không khả dụng.", any other status shows "Đăng nhập thất bại.", and a request that fails to complete shows "Không thể kết nối tới máy chủ."

---

## `GET /app`

Returns the chat page (`message.html`).

- **Auth:** valid session required.

**Responses**

| Code | Meaning | Body |
|---|---|---|
| `200 OK` | Session is valid. | the HTML page |
| `302 Found` | No valid session (never logged in, cookie invalid, or the server restarted with a random key). `Location: /` | Flask redirect page |

`message.html` is deliberately kept out of `static/`, otherwise anyone could fetch it without logging in.

---

## `POST /messages`

Sends a message. The server stores it through the Cassandra handler.

- **Auth:** valid session required (API style: `401`, not a redirect).
- **Sender:** the `user_id` from the session.
- **Receiver:** currently a fixed placeholder (`112233`). There is no recipient selection yet.

**Request body** (JSON)

| Field | Type | Rules |
|---|---|---|
| `content` | string | not empty and not only whitespace, at most 4000 characters. Stored exactly as sent (not trimmed). |

**Responses**

| Code | Meaning | Body |
|---|---|---|
| `204 No Content` | The Cassandra handler stored the message. | none |
| `400 Bad Request` | Body is not a JSON object (or not sent as JSON). Or `content` is missing, not a string, blank, or too long. The handler is not contacted. | empty |
| `401 Unauthorized` | No valid session. The handler is not contacted. | empty |
| `413 Request Entity Too Large` | Body larger than 64 KB. | Flask HTML page |
| `500 Internal Server Error` | The Cassandra handler was reached but reported that it failed to store the message (`ok = false`). | empty |
| `503 Service Unavailable` | The Cassandra handler could not be reached (gRPC error). | empty |

Other methods on this path return `405`.

**Example**

```bash
curl -i -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!"}' \
  http://<server-ip>:5000/messages
```

```http
HTTP/1.1 204 NO CONTENT
```

**Web client behavior (`message.js`):** `204` adds the message bubble and clears the input. `401` redirects to `/`. Any other status is logged to the browser console as `Server did not accept the message: <status>` and no bubble is added.

---

## `GET /static/<filename>`

Flask's built-in static file route. Serves files from the `static/` folder: `login.css`, `login.js`, `message.css`, `message.js`.

- **Auth:** none. Everything in `static/` is public, so never put protected pages or secrets there.

**Responses**

| Code | Meaning |
|---|---|
| `200 OK` | The file. Responses carry `Cache-Control: no-cache`, an `ETag` and `Last-Modified`, so browsers re-check on each load. |
| `304 Not Modified` | The browser's cached copy is still current (conditional request matched). No body. |
| `404 Not Found` | No such file. A request for the folder itself (`/static/`) is also `404`. Flask HTML page. |

---

## Response codes at a glance

| Code | Name | Where it occurs | Meaning in this app |
|---|---|---|---|
| `200` | OK | `/`, `/login`, `/app`, static files | Request succeeded. |
| `204` | No Content | `/messages` | Message stored. |
| `302` | Found | `/app` | Not logged in, redirected to `/`. |
| `304` | Not Modified | static files | Cached copy is still valid. |
| `400` | Bad Request | `/login`, `/messages` | Missing, malformed or oversized input. |
| `401` | Unauthorized | `/login`, `/messages` | `/login`: wrong credentials. `/messages`: no valid session. |
| `404` | Not Found | unknown route, missing static file | Flask HTML page. |
| `405` | Method Not Allowed | any route, wrong method | The `Allow` header lists the accepted methods. Flask HTML page. |
| `413` | Request Entity Too Large | `/login`, `/messages` | Body over 64 KB. Flask HTML page. |
| `500` | Internal Server Error | `/messages` | The Cassandra handler reported a failed write. An unexpected crash also produces `500` (Flask HTML page). |
| `503` | Service Unavailable | `/login`, `/messages` | A backend handler (MySQL for login, Cassandra for messages) is unreachable. |

---

## Internal gRPC services

These are not exposed to browsers. The server calls them from `localhost`, using channels created once at startup.

| Service | Address | Call | Used by | Notes |
|---|---|---|---|---|
| `MySQLHandler` | `localhost:50052` | `Login(LoginRequest{username, password}) → LoginResponse{ok}` | `authenticate()` for `POST /login` | **Not called yet** (`authenticate()` is a stub). Intended: a gRPC error becomes `503`. |
| `CassandraHandler` | `localhost:50051` | `AddMessage(AddMessageRequest{senderID, receiverID, content}) → AddMessageRespond{ok, err}` | `POST /messages` | `ok = false` becomes `500`. A gRPC error becomes `503`. No timeout set. |

## Current limitations

- **`authenticate()` is still a stub.** It does not call the MySQL handler yet and returns a fixed user (`user_id` 69420) for any input, so every login succeeds and the `401` and `503` responses of `POST /login` cannot occur yet. The MySQL handler's `LoginResponse` also has no `user_id`, so the proto needs extending before `authenticate()` can return the dict it promises.
- `receiverID` is hardcoded (see `POST /messages`).
- No logout endpoint, no login rate limiting, and the gRPC services listen on all interfaces.
- Plain HTTP only: passwords and the session cookie are visible to anyone who can sniff the network.

## Changelog

Add an entry here whenever a route, status code, limit or response body changes.

- **2026-10-18** – Initial version. Reflects: sessions based on `user_id`; `login_required` / `api_login_required`; input validation and size limits; the `status` JSON field removed (status codes only, `204` for sent messages).