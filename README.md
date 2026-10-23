# Flask Chat Server: Project Structure (AI Generated)

Flask server organized in **layers** and **modules**.

- **Layers:** `routes → services → repositories` (HTTP, business rules, database driver).
- **Modules:** `auth`, `users`, `relationships`, `conversations`. Each module has its own `routes.py` and `services.py`.
- **Data access is shared:** all database code lives in `src/app/shared/repositories/`, one file per table, grouped by database (MySQL, Cassandra).

> **Status:** skeleton. The `.py` files are empty. Files marked `(planned)` are decided but not created yet.

---

## 1. Folder tree

```
TemplateFileStructure/
├── README.md
├── requirements.txt                 # Python dependencies
├── .proto/                          # (empty, purpose to be decided, see section 7)
│
├── src/
│   └── app/
│       ├── __init__.py              # App factory: create_app(), registers blueprints
│       ├── server.py                # Entry point: starts the app
│       │
│       ├── auth/                    # Login, register, logout, session/token
│       │   ├── routes.py
│       │   └── services.py
│       │
│       ├── users/                   # User profile and user lookup
│       │   ├── routes.py
│       │   ├── services.py
│       │   └── repositories.py      # LEFTOVER: move to shared/repositories/mysql/user.py, then delete
│       │
│       ├── relationships/           # Friends, friend requests, blocking
│       │   ├── routes.py
│       │   └── services.py
│       │
│       ├── conversations/           # Chats (1-1 and group) and messages
│       │   ├── routes.py
│       │   └── services.py
│       │
│       └── shared/                  # Code used by more than one module
│           └── repositories/        # ALL database access
│               ├── mysql/
│               │   ├── connection.py            (planned) pool + transaction()
│               │   ├── user.py                  (planned) table: user
│               │   ├── conversation.py          (planned) table: conversation
│               │   ├── conversation_member.py   (planned) table: conversation_member
│               │   └── friendship.py            (planned) table: friendship
│               └── cassandra/
│                   ├── connection.py            (planned) session setup
│                   └── message.py               (planned) table: messages
│
├── templates/                       # HTML pages rendered by Flask (Jinja2)
│   ├── login.html
│   ├── register.html
│   └── chat.html
│
├── static/                          # CSS and JS served to the browser
│   ├── auth/
│   │   ├── login/                   # login.css, login.js
│   │   ├── register/                # register.css, register.js
│   │   └── logout/                  # (empty)
│   └── chat/                        # chat.css, chat.js
│
└── tests/                           # Automated tests (empty)
```

---

## 2. Request flow

```
Browser
   │  HTTP request
   ▼
server.py                                 entry point
   │
   ▼
routes.py                                 module: receives the request, returns the response
   │
   ▼
services.py                               module: business rules
   │
   ▼
shared/repositories/<database>/<table>.py shared: reads and writes one table
   │
   ▼
MySQL / Cassandra
```

`server.py` and `__init__.py` run once at startup (create the app, register each module's blueprint). They are not part of each request.

Calls go **downward only**. A lower layer never imports a higher one, and a route never touches a repository directly.

---

## 3. What each folder and file is for

### `src/app/` (application code)

| Path          | Role                                                                                                                 |
| ------------- | -------------------------------------------------------------------------------------------------------------------- |
| `__init__.py` | App factory. Creates the Flask app, loads config, initializes the database, registers the blueprint of every module. |
| `server.py`   | Entry point. Imports the app and runs it.                                                                            |

### Modules (`auth/`, `users/`, `relationships/`, `conversations/`)

Each module has the same two files:

| File          | Layer          | Role                           | Contains                                                                                                                                          | Does not contain                      |
| ------------- | -------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `routes.py`   | Presentation   | HTTP entry point of the module | Flask `Blueprint`, URL rules, reading `request`, basic input validation, calling a service, returning JSON/HTML and status codes                  | Business rules, SQL/CQL               |
| `services.py` | Business logic | The decisions of the module    | Calling repositories, calling other modules' services | `request`/`response` objects, SQL/CQL |

| Module          | Responsibility                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------------- |
| `auth`          | Proving who the user is: register, login, logout, password check, session                    |
| `users`         | User profile (display name, avatar), user lookup and search                                |
| `relationships` | Links between two users: friend requests, friend list, remove friend, block                             |
| `conversations` | Chats and their messages: create 1-1 or group chat, member roles, send and load messages, unread counts |

### `shared/repositories/` (data access)

Only code in this folder talks to a database. It is **grouped by database, then one file per table**.

| Path                      | Role                                                                                                                                             |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `mysql/connection.py`     | MySQL connection pool and the `transaction()` helper used for multi-table writes                                                                 |
| `mysql/<table>.py`        | Functions for one MySQL table: `get_by_id`, `insert`, `update`, `list_...`, plus read-only joins that return this entity                         |
| `cassandra/connection.py` | Cassandra session setup                                                                                                                          |
| `cassandra/<table>.py`    | Functions for one Cassandra table. Cassandra tables are built around a query, so name the file after the access pattern if you add more than one |

Repository functions contain **data access only**: no business rules, nothing about HTTP.

**Table ownership** (only the owner writes to a table):

| Table                                 | Database  | Owner module    |
| ------------------------------------- | --------- | --------------- |
| `user`                                | MySQL     | `users`         |
| `friendship`                          | MySQL     | `relationships` |
| `conversation`, `conversation_member` | MySQL     | `conversations` |
| `message`                             | Cassandra | `conversations` |
| sessions / tokens (if needed)         | MySQL     | `auth`          |

### Frontend

| Path                                                          | Role                                                                                               |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `templates/login.html`, `register.html`                       | Pages of the `auth` module                                                                         |
| `templates/chat.html`                                         | Page of the `conversations` module                                                                 |
| `static/auth/login/`, `static/auth/register/`, `static/chat/` | CSS and JS for each page, same grouping as the templates. Loaded by the browser from `/static/...` |
| `static/auth/logout/`                                         | Empty. Logout probably needs only a route                                                          |

### Other

| Path               | Role                                                                               |
| ------------------ | ---------------------------------------------------------------------------------- |
| `requirements.txt` | pip packages (Flask, MySQL driver, Cassandra driver, ...)                          |
| `tests/`           | Automated tests, ideally mirroring `src/app/` (`tests/auth/`, `tests/users/`, ...) |
| `.proto/`          | Empty, see section 7                                                               |

---

## 4. Rules to keep the structure clean

1. **Layers go downward only:** `routes → services → repositories`.
2. **Only the owner writes a table.** Example: only `conversation_member.py` inserts, updates or deletes `conversation_member` rows. Other code may read it, including through joins.
3. **Put a join in the repository of the main entity it returns.** Example: the member list with names goes in `conversation_member.py`.
4. **Don't copy a business rule into a second module.** If `conversations` needs "are these two users friends?", it calls `relationships.services.are_friends()`. It does not read `friendship` and re-implement the check.
5. **Repositories hold data access only.** Business rules stay in `services.py`.
6. **Multi-table writes use one transaction.** Repository functions accept a connection or transaction from `mysql/connection.py`. Example: creating a conversation writes `conversation` and `conversation_member` together.
7. **Cassandra cannot join.** To show a message with the sender's name, fetch the messages, then fetch the users in one batch (`user.get_many(ids)`). Never one query per message.
8. **Keep module dependencies one-way.** Suggested direction: `conversations → relationships → users`, and `auth → users`. `users` depends on no other module. If two modules need each other, orchestrate both steps from one higher-level service or route instead.

---

## 5. Why this layout

Chat screens need data from many tables at once (conversation list, member list, friend list), and messages live in a different database anyway. Keeping data access in one shared place makes joins and transactions simple. The cost is that any service _can_ reach any table, which is why rules 2 to 4 matter.

## 6. If it gets messy: scaling path

Add a `repositories.py` to **one module only** (not all). It sits on top of the shared table files and hides transactions and the MySQL/Cassandra split from that module's services:

```
conversations/
├── routes.py
├── services.py
└── repositories.py     # e.g. create_with_members(), get_recent_messages()
```

Signs it is time: services repeat transaction code, services mix MySQL and Cassandra calls, or several developers keep editing the same shared files. The shared table files do not change when you do this. Only if you plan to split modules into separate services would you later move each table file into its owning module.
