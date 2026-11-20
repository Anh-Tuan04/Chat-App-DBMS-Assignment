# Flask Chat Server: Project Structure (AI Generated)

This project is a Flask chat application. The backend is organized by technical
layer under `src/modules`:

`controllers -> services -> repositories`

The controllers expose HTTP endpoints, services contain application logic, and
repositories provide the data-access layer. Some backend modules are still
skeletons, while the frontend contains the current chat, authentication, and
API documentation files.

> **Status:** in development. Several files are placeholders or contain
> commented-out integrations, so this document describes the current
> repository rather than a planned structure.

---

## 1. Folder tree

```text
TemplateFileStructure_branch/
├── README.md
├── requirements.txt
├── server.py
├── .env
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── utils.py
│   ├── modules/
│   │   ├── controllers/
│   │   │   ├── auth.py
│   │   │   ├── conversations.py
│   │   │   ├── messages.py
│   │   │   ├── notifications.py
│   │   │   ├── relationships.py
│   │   │   └── users.py
│   │   ├── services/
│   │   │   ├── auth.py
│   │   │   ├── conversations.py
│   │   │   ├── messages.py
│   │   │   ├── notifications.py
│   │   │   ├── relationships.py
│   │   │   └── users.py
│   │   ├── repositories/
│   │   │   ├── auth.py
│   │   │   ├── conversations.py
│   │   │   ├── messages.py
│   │   │   ├── notifications.py
│   │   │   ├── relationships.py
│   │   │   └── users.py
│   │   └── real_time_socket/
│   │       ├── __init__.py
│   │       ├── extensions.py
│   │       ├── events/
│   │       │   ├── connection.py
│   │       │   ├── messages.py
│   │       │   └── notifications.py
│   │       └── emitters/
│   │           └── notifications.py
│   ├── shared/
│   │   ├── error.py
│   │   ├── ids.py
│   │   └── repositories/
│   │       ├── cassandra/
│   │       └── mysql/
│   └── users/
│       ├── routes.py
│       └── services.py
│
├── templates/
│   ├── chat.html
│   ├── login.html
│   └── register.html
│
├── static/
│   ├── auth/
│   │   ├── login/
│   │   │   ├── login.css
│   │   │   ├── login.js
│   │   │   └── login-api.md
│   │   ├── logout/
│   │   │   └── logout-api.md
│   │   └── register/
│   │       ├── register.css
│   │       ├── register.js
│   │       └── register-api.md
│   │
│   └── chat/
│       ├── chat.css
│       ├── chat.js
│       ├── conversation.js
│       ├── error.js
│       ├── toast.js
│       ├── conversations/
│       │   ├── create-new-conversation-api.md
│       │   └── get-conversations-api.md
│       ├── relationships/
│       │   ├── accept-friend-api.md
│       │   ├── get-friend-request-api.md
│       │   ├── get-friends-api.md
│       │   └── make-friend-api.md
│       ├── top-right-bar/
│       │   ├── add-friend.js
│       │   ├── create-group.js
│       │   ├── friends.js
│       │   ├── notifications.js
│       │   └── user-profile.js
│       └── users/
│           └── search-user-api.md
```

---

## 2. Application startup and request flow

```text
server.py
   │
   ▼
create_app() in server.py
   │
   ├── registers src/modules/controllers blueprints
   ├── registers src/users/routes.py
   └── initializes src/modules/real_time_socket
   │
   ▼
controller / route
   │
   ▼
service
   │
   ▼
repository
   │
   ▼
MySQL or Cassandra
```

`server.py` at the workspace root is the development entry point. It adds `src`
to Python's import path, creates the Flask application, registers the enabled
blueprints, initializes Flask-SocketIO, and starts the server.

At present, the authentication controller is enabled. The other controllers
are present but their blueprint registrations are commented out. The separate
`src/users` package is also registered directly and should be treated as a
legacy or transitional implementation until it is merged into `src/modules`.

---

## 3. Backend folders and files

### `src/modules/controllers/`

Controllers define Flask blueprints (testing in advance), URL rules, request parsing, basic input
validation, and HTTP responses.

| File               | Responsibility                                |
| ------------------ | --------------------------------------------- |
| `auth.py`          | Authentication endpoints such as registration |
| `conversations.py` | Conversation and chat endpoints               |
| `messages.py`      | Message endpoints                             |
| `notifications.py` | Notification endpoints                        |
| `relationships.py` | Friend and relationship endpoints             |
| `users.py`         | User endpoints                                |

### `src/modules/services/`

Services are the application/business-logic layer. They should receive
validated values from controllers and coordinate repository operations without
depending on Flask request or response objects.

### `src/modules/repositories/`

Repositories are grouped by feature and contain the data-access abstractions
used by the services:

| File               | Responsibility                                  |
| ------------------ | ----------------------------------------------- |
| `auth.py`          | User credentials and authentication persistence |
| `conversations.py` | Conversation persistence                        |
| `messages.py`      | Message persistence                             |
| `notifications.py` | Notification persistence                        |
| `relationships.py` | Friend and relationship persistence             |
| `users.py`         | User persistence and lookup                     |

### `src/shared/repositories/`

This folder contains database-specific table implementations shared by the
feature repositories:

- `mysql/` contains MySQL connection and table implementations.
- `cassandra/` contains Cassandra table implementations.
- `conversations.py` combines shared conversation repository implementations.

### `src/modules/real_time_socket/`

This package contains Flask-SocketIO setup:

- `extensions.py` creates the shared `SocketIO` instance.
- `events/` registers connection and real-time message/notification handlers.
- `emitters/` sends real-time notification payloads to connected clients.

### `src/users/`

This is a separate user route/service package currently registered by
`create_app()`. This is used for testing before plugging in frontend.

---

## 4. Frontend folders

| Path                      | Role                                           |
| ------------------------- | ---------------------------------------------- |
| `templates/login.html`    | Login page                                     |
| `templates/register.html` | Registration page                              |
| `templates/chat.html`     | Main chat page                                 |
| `static/auth/login/`      | Login assets and login API notes               |
| `static/auth/register/`   | Registration assets and registration API notes |
| `static/auth/logout/`     | Logout API notes                               |
| `static/chat/`            | Chat UI assets and feature API notes           |
| `static/chat/top-right-bar/` | Top-right chat controls and related scripts |

The frontend is split into feature files under `static/chat/`. For example,
conversation behavior is in `conversation.js`, while the friend, notification,
group, and profile-menu behavior is organized under
`static/chat/top-right-bar/`.

---

## 5. Rules for keeping the structure consistent

1. Keep HTTP-specific code in `modules/controllers`.
2. Keep business and application logic in `modules/services`.
3. Keep persistence and database access in `modules/repositories` or
   `shared/repositories`.
4. Controllers should call services instead of implementing business rules.
5. Services should not read Flask's `request` or construct HTTP responses.
6. Reuse shared database helpers instead of duplicating connection logic.
