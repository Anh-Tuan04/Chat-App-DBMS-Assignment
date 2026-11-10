# Flask Chat Server: Project Structure (AI Generated)

This project is a Flask chat application. The backend is currently organized
by technical layer under `src/app/modules`:

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
TemplateFileStructure/
├── README.md
├── requirements.txt
│
├── src/
│   └── app/
│       ├── __init__.py
│       ├── server.py
│       │
│       ├── modules/
│       │   ├── controllers/
│       │   │   ├── auth.py
│       │   │   ├── conversations.py
│       │   │   ├── messages.py
│       │   │   ├── notifications.py
│       │   │   ├── relationships.py
│       │   │   └── users.py
│       │   │
│       │   ├── services/
│       │   │   ├── auth.py
│       │   │   ├── conversations.py
│       │   │   ├── messages.py
│       │   │   ├── notifications.py
│       │   │   ├── relationships.py
│       │   │   └── users.py
│       │   │
│       │   └── repositories/
│       │       ├── auth.py
│       │       ├── conversations.py
│       │       ├── messages.py
│       │       ├── notifications.py
│       │       ├── relationships.py
│       │       └── users.py
│       │
│       ├── shared/
│       │   └── repositories/
│       │       ├── cassandra/
│       │       │   └── messages.table.py
│       │       └── mysql/
│       │           └── conversations.table.py
│       │
│       └── users/
│           ├── routes.py
│           └── services.py
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
│       ├── add-friend.js
│       ├── error.js
│       ├── friends.js
│       ├── toast.js
│       ├── user-profile.js
│       ├── conversations/
│       │   ├── create-new-conversation-api.md
│       │   └── get-conversations-api.md
│       ├── notifications/
│       │   └── notifications.js
│       ├── relationships/
│       │   ├── accept-friend-api.md
│       │   ├── get-friend-request-api.md
│       │   ├── get-friends-api.md
│       │   └── make-friend-api.md
│       └── users/
│           └── search-user-api.md
```

---

## 2. Application startup and request flow

```text
server.py
   │
   ▼
create_app() in app/__init__.py
   │
   ├── registers modules.controllers.auth.auth_bp
   └── registers app.users.routes.users_routes_bp
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

`src/app/server.py` is the development entry point. The application factory
in `src/app/__init__.py` configures Flask's `/static` directory and registers
the currently enabled blueprints.

At present, the authentication controller is enabled. The other controllers
are present but their blueprint registrations are commented out. The separate
`src/app/users` package is also registered directly and should be treated as a
legacy or transitional implementation until it is merged into
`src/app/modules`.

---

## 3. Backend folders and files

### `src/app/modules/controllers/`

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

### `src/app/modules/services/`

Services are the application/business-logic layer. They should receive
validated values from controllers and coordinate repository operations without
depending on Flask request or response objects.

### `src/app/modules/repositories/`

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

### `src/app/shared/repositories/`

This folder contains database-specific table implementations shared by the
feature repositories:

- `mysql/conversations.table.py` contains MySQL conversation-table access.
- `cassandra/messages.table.py` contains Cassandra message-table access.

### `src/app/users/`

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

The frontend is split into feature files under `static/chat/`. For example,
conversation behavior is in `conversation.js`, friend behavior is in
`friends.js`, and profile-menu behavior is in `user-profile.js`.

---

## 5. Rules for keeping the structure consistent

1. Keep HTTP-specific code in `modules/controllers`.
2. Keep business and application logic in `modules/services`.
3. Keep persistence and database access in `modules/repositories` or
   `shared/repositories`.
4. Controllers should call services instead of implementing business rules.
5. Services should not read Flask's `request` or construct HTTP responses.
6. Reuse shared database helpers instead of duplicating connection logic.
