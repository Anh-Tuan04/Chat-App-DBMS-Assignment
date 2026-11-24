# Flask Chat App (MySQL + Cassandra)

A real-time chat web app with friends, friend requests, blocking, notifications,
1-1 and group conversations, and messages.

- **Backend:** Flask + Flask-SocketIO (Python)
- **Databases:** MySQL stores users, relationships, notifications and
  conversations. Cassandra stores messages and per-user conversation lists.
- **Frontend:** plain HTML in `templates/` and native ES modules in `static/`.
  There is no build step.

Contents:

1. [Folder tree and layout](#1-folder-tree-and-layout)
2. [Prerequisites](#2-prerequisites)
3. [Start the databases with Docker Compose](#3-start-the-databases-with-docker-compose)
4. [Connect MySQL Workbench](#4-connect-mysql-workbench)
5. [Run the web server](#5-run-the-web-server)
6. [Open the app in a browser](#6-open-the-app-in-a-browser)
7. [Log in as several users on one machine (separate cookie jars)](#7-log-in-as-several-users-on-one-machine-separate-cookie-jars)
8. [Stopping and resetting](#8-stopping-and-resetting)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Folder tree and layout

### 1.1 Folder tree

```text
.
├── server.py
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── README.md
├── LICENSE
│
├── src/
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
│   │   │   ├── container.py
│   │   │   ├── auth.py
│   │   │   ├── conversations.py
│   │   │   ├── messages.py
│   │   │   ├── notifications.py
│   │   │   ├── relationships.py
│   │   │   └── users.py
│   │   ├── repositories/
│   │   └── real_time_socket/
│   │       ├── extensions.py
│   │       ├── events/
│   │       └── emitters/
│   ├── shared/
│   │   ├── ids.py
│   │   └── repositories/
│   │       ├── conversations.py
│   │       ├── mysql/
│   │       └── cassandra/
│   └── users/
│       └── routes.py
│
├── templates/
│   ├── login.html
│   ├── register.html
│   └── chat.html
│
├── static/
│   ├── auth/
│   └── chat/
│       ├── chat.js
│       ├── chat.css
│       ├── real-time-socket.js
│       ├── conversation.js
│       ├── sidebar-search.js
│       ├── toast.js
│       ├── error.js
│       ├── chat-area/
│       ├── top-right-bar/
│       └── api-descriptions/
│
└── tests/
```

### 1.2 Layout

**Root files**

| Path | Description |
| --- | --- |
| `server.py` | Entry point. Loads `.env`, adds `src/` to the import path, builds the Flask app and starts Flask-SocketIO on port 5000. |
| `requirements.txt` | Python dependencies. |
| `docker-compose.yml` | MySQL (3306), Cassandra (9042) and a one-shot container that loads the Cassandra schema. |
| `.env.example` | Template for `.env` (database connection settings). |
| `LICENSE` | MIT license. |

**Backend (`src/`)**

| Path | Description |
| --- | --- |
| `src/utils.py` | Shared helpers: `login_required`, `error_response` and the session interface. |
| `src/modules/controllers/` | Flask blueprints under `/api/...`. They parse and validate the request, call a service, and map the service's errors to HTTP status codes. One file per feature. |
| `src/modules/services/` | Business logic, one file per feature. Services never use Flask's `request` or build responses. |
| `src/modules/services/container.py` | Composition root. Builds every repository and service once when the app starts. |
| `src/modules/repositories/` | Repository interfaces (abstract classes) and dataclasses. |
| `src/modules/real_time_socket/extensions.py` | The shared `socketio` instance. |
| `src/modules/real_time_socket/events/` | `@socketio.on` handlers: connect, messages, conversations, notifications. |
| `src/modules/real_time_socket/emitters/` | Push events to each user's `user:{id}` room. |
| `src/shared/ids.py` | Snowflake ID generator for message and notification IDs. |
| `src/shared/repositories/mysql/` | MySQL repository implementations and `schema.sql` (tables and triggers). |
| `src/shared/repositories/cassandra/` | Cassandra repository implementations and `schema.cql`. |
| `src/shared/repositories/conversations.py` | Combines the MySQL and Cassandra conversation repositories into one. |
| `src/users/routes.py` | Serves the HTML pages `/`, `/register` and `/chat`. |

**Frontend**

| Path | Description |
| --- | --- |
| `templates/` | Plain HTML pages (not Jinja templates): login, register and chat. |
| `static/auth/` | Scripts and styles for login, register and logout, plus their API notes (`*-api.md`). |
| `static/chat/chat.js` | Entry module of the chat page. It wires up the modals. |
| `static/chat/chat.css` | Styles for the chat page. |
| `static/chat/real-time-socket.js` | The single socket.io client connection. |
| `static/chat/conversation.js` | Conversation list in the left sidebar. |
| `static/chat/sidebar-search.js` | Search box in the sidebar. |
| `static/chat/toast.js`, `error.js` | Toast messages and error display. |
| `static/chat/chat-area/` | Message stream and message actions. |
| `static/chat/top-right-bar/` | Friends, add friend, notifications, groups, blocked users and profile. |
| `static/chat/api-descriptions/` | API contracts (request and response shapes) for each feature. |

**Other**

| Path | Description |
| --- | --- |
| `tests/` | Empty for now. |

**How a request flows through the backend:**

```text
Browser ──HTTP /api/...──► controller ──► service ──► repository ──► MySQL / Cassandra
        ◄──socket.io────── emitters ◄──────┘
```

- Controllers parse and validate the request, call a service, and turn the
  service's error strings into HTTP status codes.
- Services hold the business logic. They return errors instead of raising them.
- Repositories talk to the databases. The interfaces are in
  `src/modules/repositories/` and the implementations are in
  `src/shared/repositories/mysql/` and `.../cassandra/`.
- The API contracts are in `static/chat/api-descriptions/**/*.md` and
  `static/auth/*/*-api.md`.

---

## 2. Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose v2) | Recent version | Running MySQL and Cassandra |
| [Python](https://www.python.org/downloads/) | **3.10 or newer** (developed on 3.12) | Running the Flask server. The code uses `match` and `X \| None`, which need 3.10+. |
| [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) | 8.0 or newer | Optional: browsing and querying the MySQL database |
| A modern browser (Chrome, Edge, Firefox) | Recent version | Using the app |
| Git | Any | Cloning the repository |

Hardware: Cassandra needs about **1–2 GB of free RAM**. On Windows, give Docker
Desktop enough memory (Settings → Resources if you use the Hyper-V backend, or
`.wslconfig` if you use the WSL 2 backend).

Free ports needed: **3306** (MySQL), **9042** (Cassandra) and **5000** (web server).

---

## 3. Start the databases with Docker Compose

1. Start **Docker Desktop** and wait until it says *Engine running*.
2. Open a terminal in the project root (the folder that contains
   `docker-compose.yml`) and run:

   ```sh
   docker compose up -d
   ```

   This starts three containers:

   | Service | What it does |
   | --- | --- |
   | `mysql` | MySQL on `localhost:3306`. User `root` with an **empty password**. Database `chatapp`. On first start it runs `src/shared/repositories/mysql/schema.sql` (tables and triggers). |
   | `cassandra` | Cassandra on `localhost:9042`. |
   | `cassandra-init` | Waits until Cassandra is healthy, runs `src/shared/repositories/cassandra/schema.cql` (keyspace `chat_app` and its tables), then exits. |

3. Wait until everything is ready. Cassandra usually needs **1–2 minutes** on
   its first start.

   ```sh
   docker compose ps -a
   ```

   You are ready when `mysql` and `cassandra` show `(healthy)` and
   `cassandra-init` shows `Exited (0)`. If `cassandra-init` exited with another
   code, check its log with `docker compose logs cassandra-init`.

4. Optional checks from the command line:

   ```sh
   # MySQL: should list the tables
   docker compose exec mysql mysql -uroot chatapp -e "SHOW TABLES;"

   # Cassandra: should list the tables of the chat_app keyspace
   docker compose exec cassandra cqlsh -e "DESCRIBE TABLES;" -k chat_app
   ```

> **Note:** the schema files are only applied when the Docker volumes are
> **created for the first time**. If a schema file changes later, reset the
> volumes (see [Stopping and resetting](#8-stopping-and-resetting)) or apply the
> change by hand.

---

## 4. Connect MySQL Workbench

1. Open MySQL Workbench. On the home screen, click the **⊕** next to
   **MySQL Connections**.
2. Fill in the dialog:

   | Field | Value |
   | --- | --- |
   | Connection Name | `chatapp (docker)` (any name) |
   | Connection Method | Standard (TCP/IP) |
   | Hostname | `127.0.0.1` |
   | Port | `3306` |
   | Username | `root` |
   | Password | leave empty (do not store one) |
   | Default Schema | `chatapp` |

3. Click **Test Connection**, then **OK**.
   - The image is `mysql:latest` (MySQL 9.x). Workbench 8.0 may warn that the
     server version is not supported. Click **Continue Anyway**. Browsing and
     querying work normally.
4. Open the connection. The `chatapp` schema shows the tables `users`,
   `friend_requests`, `friendships`, `blocks`, `notifications`,
   `conversations`, `channels` and `channel_members`. The triggers are under
   each table's **Triggers** node.

The MySQL container must be running for Workbench to connect.

---

## 5. Run the web server

1. **Create the `.env` file.** Copy the example:

   ```sh
   # Windows (PowerShell)
   Copy-Item .env.example .env
   # macOS / Linux
   cp .env.example .env
   ```

   Then edit `.env` so that it matches the Docker containers. The MySQL
   container uses `root` with an empty password:

   ```ini
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_DATABASE=chatapp

   CASSANDRA_CONTACT_POINTS=127.0.0.1
   CASSANDRA_PORT=9042
   CASSANDRA_KEYSPACE=chat_app
   ```

2. **Create a virtual environment and install the dependencies:**

   ```sh
   python -m venv .venv
   ```

   Activate it:

   | Shell | Command |
   | --- | --- |
   | Windows cmd | `.venv\Scripts\activate.bat` |
   | Windows PowerShell | `.venv\Scripts\Activate.ps1` |
   | macOS / Linux | `source .venv/bin/activate` |

   Then install:

   ```sh
   python -m pip install -r requirements.txt
   ```

   If PowerShell refuses to run `Activate.ps1`, run
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use cmd.

3. **Start the server** (with the databases from step 3 running):

   ```sh
   python -m server
   ```

   The server listens on `0.0.0.0:5000` and prints each request and response
   in the terminal. Stop it with `Ctrl+C`.

   The server connects to Cassandra when it starts. **It will not start if
   Cassandra is not up yet.** If startup fails with a Cassandra connection
   error, wait until `docker compose ps -a` shows Cassandra as healthy and try
   again.

---

## 6. Open the app in a browser

| URL | Page |
| --- | --- |
| <http://localhost:5000/> | Login page. It redirects to `/chat` if you are already logged in. |
| <http://localhost:5000/register> | Create an account |
| <http://localhost:5000/chat> | Chat page. It redirects to the login page if you are not logged in. |

To try the app:

1. Register two or more accounts on `/register`.
2. Log in, then use the top-right bar to send friend requests, accept them,
   create groups, and so on.
3. Open a conversation and send messages. Messages and notifications arrive in
   real time over socket.io.

To use the app from another device on the same network, open
`http://<your-computer's-LAN-IP>:5000` (allow port 5000 through the firewall).

> **Restarting the server logs everyone out.** The session signing key is
> generated randomly each time the server starts, so existing session cookies
> stop being valid. Just log in again.

---

## 7. Log in as several users on one machine (separate cookie jars)

Your login is kept in a session cookie. Browsers store cookies **per
hostname** (the port is ignored), and all normal tabs and windows of one
browser profile share them. So if you log in as *Alice* in one tab and as *Bob*
in another tab on `http://localhost:5000`, the second login replaces the first
one in both tabs.

To test a chat between users on one machine, give each user its **own cookie
jar** in one of these ways:

### Option A: use a different hostname for each user (one browser, no setup)

The server listens on every interface, so the same server can be opened under
several hostnames. Each hostname gets its own cookies:

| User | URL |
| --- | --- |
| User 1 | <http://localhost:5000> |
| User 2 | <http://127.0.0.1:5000> |
| User 3 | <http://127.0.0.2:5000> |
| User 4 | <http://127.0.0.3:5000> |
| … | `http://<your LAN IP>:5000` |

Any `127.x.x.x` address points to your own machine on Windows and Linux. On
macOS only `127.0.0.1` works unless you add more loopback aliases, so use
`localhost`, `127.0.0.1` and your LAN IP there.

> Changing only the port does **not** work (`localhost:5000` and
> `localhost:5001` share cookies). The **hostname** must be different.

### Option B: private / incognito window

Open a private window (`Ctrl+Shift+N` in Chrome and Edge, `Ctrl+Shift+P` in
Firefox). It has a separate cookie jar from the normal windows. All private
windows of the same browser **share one jar**, so this gives you only one extra
user. Closing every private window deletes that jar.

### Option C: browser profiles or containers

- **Chrome / Edge:** create extra profiles (profile icon → *Add*). Each profile
  has its own cookies and opens in its own window.
- **Firefox:** install the **Multi-Account Containers** extension and open each
  user in a different container tab, all in the same window.

### Option D: different browsers

For example, Chrome for user 1, Edge for user 2 and Firefox for user 3.

You can combine these options. For example, `localhost` and `127.0.0.1` in a
normal window plus the same two hostnames in a private window gives four users
in one browser.

---

## 8. Stopping and resetting

```sh
# Stop the containers but keep the data
docker compose stop

# Start them again later
docker compose start

# Remove the containers but keep the data volumes
docker compose down

# Remove the containers AND all data, then rebuild both schemas from scratch
docker compose down -v
docker compose up -d
```

Use `down -v` after changing `schema.sql` or `schema.cql`, or whenever you want
an empty database. **It deletes every user, message and conversation.**

---

## 9. Troubleshooting

| Problem | Fix |
| --- | --- |
| `docker compose up` says port 3306 is already in use | A local MySQL installation is using the port. Stop that MySQL service (Windows: *Services* → `MySQL80` → Stop), or change the mapping in `docker-compose.yml` to `3307:3306` and set `MYSQL_PORT=3307` in `.env` and in Workbench. |
| Port 9042 or 5000 is already in use | Stop the program that uses it, or change the port mapping. |
| The server fails at startup with a Cassandra `NoHostAvailable` error | Cassandra is still starting. Wait until it is `(healthy)` and `cassandra-init` has exited with code 0, then start the server again. |
| `Keyspace 'chat_app' does not exist` | `cassandra-init` did not finish. Run `docker compose logs cassandra-init`, then `docker compose up -d cassandra-init` to run it again. |
| MySQL `Access denied for user ...` | Check that `.env` contains `MYSQL_USER=root` and an empty `MYSQL_PASSWORD=`. |
| MySQL error `Table 'chatapp.xxx' doesn't exist` | The volume was created before the schema existed or changed. Reset it with `docker compose down -v` and `docker compose up -d`. |
| The Cassandra container keeps restarting or exits with code 137 | It ran out of memory. Give Docker Desktop more memory. |
| Two tabs keep switching to the same user | That is expected: both tabs share one cookie jar. See [section 7](#7-log-in-as-several-users-on-one-machine-separate-cookie-jars). |
| Logged out after restarting the server | That is expected: the session key changes on every start. Log in again. |

---

## License

This project is released under the [MIT License](LICENSE).
