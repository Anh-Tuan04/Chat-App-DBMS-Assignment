import {
  appendIncomingMessage,
  renderMessageHistory,
  getOldestMessageId,
  prependOlderMessages
} from './messages-stream-adapter.js';
import { createNewMessageStream, clearMessageStream } from './messages-stream.js';
import { realTimeSocket } from '../real-time-socket.js';
import {
  conversationList,
  handleNewMessageComing,
  getConversations,
  findConversationItemByReceiverId,
  updateConversationPreview,
  addConversationItem,
  setActiveConversationItem,
  clearConversationUnread,
  getConversationName
} from '../conversation.js';
import { showError } from '../error.js';

/* The open chat: opening a conversation, the first page, older pages (scroll up), marking
   read, sending and receiving. The sidebar list itself is in ../conversation.js, which
   never imports this file. */



const currentUser = JSON.parse(
  localStorage.getItem('user') || '{}'
);
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-btn');
export const messageStreamElement = document.getElementById('message-stream');

const ACK_TIMEOUT_MS = 10000;

const MESSAGES_PAGE_LIMIT = 30;

// Sends "read up to this message" for a conversation. lastMessageId: the newest message the user has seen.
// Returns true when the server confirmed. Errors are shown, never thrown.
const markConversationRead = async (conversationId, lastMessageId) => {
    if (!realTimeSocket.connected) return false;
    try {
        const response = await realTimeSocket
            .timeout(ACK_TIMEOUT_MS)
            .emitWithAck('mark_read', {
                conversation_id: conversationId,
                last_message_id: lastMessageId
            });

        if (response.status !== 'success') {
            showError(response.message);
            return false;
        }
        return true;
    } catch (error) {
        showError('The server did not respond. Could not mark the conversation as read.');
        return false;
    }
};

// ---------- Older messages (scroll up) ----------
const OLDER_SCROLL_THRESHOLD_PX = 120;   // start loading when the top is this close
let isLoadingOlder = false;
let hasOlderMessages = true;             // false once a page has fewer items than the limit
let olderRequestId = 0;                  // a new conversation invalidates the running request

const resetOlderMessages = () => {
    olderRequestId += 1;
    isLoadingOlder = false;
    hasOlderMessages = true;
};

// GET /api/messages?conversation_id=..&before=<oldest id on screen>&limit=..
const loadOlderMessages = async () => {
    const conversationId = messageStreamElement.dataset.conversationId;
    if (!conversationId || isLoadingOlder || !hasOlderMessages) return;

    const oldestMessageId = getOldestMessageId(messageStreamElement);
    if (!oldestMessageId) return;

    isLoadingOlder = true;
    const requestId = olderRequestId;
    try {
        const response = await fetch(
            '/api/messages?conversation_id=' + encodeURIComponent(conversationId) +
            '&before=' + encodeURIComponent(oldestMessageId) +
            '&limit=' + MESSAGES_PAGE_LIMIT,
            { method: 'GET', credentials: 'include' }
        );
        const body = await response.json();

        if (requestId !== olderRequestId) return;   // another conversation was opened meanwhile
        if (!response.ok) {
            showError(body.message);
            return;
        }
        if (!Array.isArray(body)) {
            showError('Invalid messages response');
            return;
        }

        if (body.length < MESSAGES_PAGE_LIMIT) hasOlderMessages = false;   // nothing older left
        prependOlderMessages(messageStreamElement, body);
    } catch (error) {
        if (requestId === olderRequestId) showError('Failed to load older messages');
    } finally {
        if (requestId === olderRequestId) isLoadingOlder = false;
    }

    // The page did not fill the panel, so the user cannot scroll to trigger the next one
    if (requestId === olderRequestId) loadOlderMessagesIfNotScrollable();
};

const loadOlderMessagesIfNotScrollable = () => {
    if (hasOlderMessages && messageStreamElement.scrollHeight <= messageStreamElement.clientHeight) {
        loadOlderMessages();
    }
};

// One scroll listener for the stream
messageStreamElement.addEventListener('scroll', () => {
    if (messageStreamElement.scrollTop <= OLDER_SCROLL_THRESHOLD_PX) loadOlderMessages();
});

// Id of the newest message on screen (messages are in the stream oldest first), or null if empty
const getNewestMessageId = () => {
    const messages = messageStreamElement.querySelectorAll('.message');
    return messages.length ? messages[messages.length - 1].dataset.messageId : null;
};

// Marks the OPEN conversation as read up to the newest message on screen,
// then removes the bold state and the badge of its sidebar row.
const markOpenConversationRead = async () => {
    const conversationId = messageStreamElement.dataset.conversationId;
    const newestMessageId = getNewestMessageId();
    if (!conversationId || !newestMessageId) return;   // nothing seen yet, nothing to mark

    const isMarkedRead = await markConversationRead(conversationId, newestMessageId);
    if (!isMarkedRead) return;

    clearConversationUnread(conversationId);
};

// Called when the user has seen new messages of the open conversation. Waits a short moment so
// several messages in a row make one request; while the tab is hidden it waits until the tab is visible.
let markReadTimer = null;
let hasPendingRead = false;
export const scheduleMarkRead = (delayMs = 300) => {
    clearTimeout(markReadTimer);
    markReadTimer = setTimeout(() => {
        if (document.hidden) {
            hasPendingRead = true;
            return;
        }
        markOpenConversationRead();
    }, delayMs);
};

document.addEventListener('visibilitychange', () => {
    if (document.hidden || !hasPendingRead) return;
    hasPendingRead = false;
    markOpenConversationRead();
});

// Opens a conversation of the sidebar: new stream, highlight, mark read, load the first page.
// conversationItem: a `.conversation-item` element of #conversation-list
export const openConversation = async (conversationItem) => {
    const conversationId = conversationItem.dataset.conversationId;
    if (messageStreamElement.dataset.conversationId === conversationId) return;   // already open

    // 1. Empty the stream; it now belongs to this conversation
    createNewMessageStream(messageStreamElement, conversationId);
    resetOlderMessages();

    // A conversation is open now: forget a receiver picked for a new chat
    delete document.getElementById('conversation-name').dataset.receiverId;

    // Sidebar: highlight this item at once
    setActiveConversationItem(conversationItem);

    // 2. Request the first page (no `before`)
    try {
        const response = await fetch(
            '/api/messages?conversation_id=' + encodeURIComponent(conversationId) +
            '&limit=' + MESSAGES_PAGE_LIMIT,
            { method: 'GET', credentials: 'include' }
        );
        const body = await response.json();

        if (!response.ok) {
            showError(body.message);
            return;
        }

        if (messageStreamElement.dataset.conversationId !== conversationId) return;

        // 3. Fill the stream
        renderMessageHistory(messageStreamElement, body);
        hasOlderMessages = body.length >= MESSAGES_PAGE_LIMIT;   // a short first page is the whole history
        loadOlderMessagesIfNotScrollable();

        // 4. Mark as read up to the newest message now on screen (after rendering, not before)
        scheduleMarkRead(0);

        document.getElementById('conversation-name').textContent = getConversationName(conversationItem);
        document.getElementById('chat-input').focus();
    } catch (error) {
        showError('Failed to load messages');
    }
};

// A user was picked (sidebar search row, friends modal). No request is sent:
//   - the sidebar already has a conversation with this user -> open it, return true
//   - otherwise -> empty composer ready for a NEW chat (the first message creates the
//     conversation, see messages-actions.js), return false
export const openChatWithUser = ({ userId, name }) => {
    const existingItem = findConversationItemByReceiverId(userId);
    if (existingItem) {
        openConversation(existingItem);
        return true;
    }

    clearMessageStream(messageStreamElement);
    resetOlderMessages();
    setActiveConversationItem(null);

    const conversationName = document.getElementById('conversation-name');
    conversationName.textContent = name;
    conversationName.dataset.receiverId = String(userId);
    document.getElementById('chat-input').focus();
    return false;
};

// One click listener for the whole list: the row says which conversation via data-conversation-id
conversationList.addEventListener('click', (event) => {
    const conversationItem = event.target.closest('.conversation-item');
    if (conversationItem) openConversation(conversationItem);
});

const handleSubmitMessage = async (messageStream) => {
  const text = chatInput.value.trim();
  if (!text) return;

  const conversationId = messageStream.dataset.conversationId;   // changed: from the stream
  if (!conversationId) {
    // No open conversation: only allowed when a user was picked in the sidebar search
    const receiverId = document.getElementById('conversation-name').dataset.receiverId;
    if (!receiverId) {
      showError('Select a conversation first.');
      return;
    }
    try {
      // create new conversation
      let res = await fetch(
        `${window.location.origin}/api/conversations/new-conversation?user_id=${encodeURIComponent(receiverId)}`,
        {
          headers: {
            'Content-Type': 'application/json'
          },
          method: 'POST',
          credentials: 'include',
          body: JSON.stringify({
            message: text
          }),
        }
      )
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        if (res.status === 409) {
          // The list did not have it yet: reload the list, then open the existing conversation.
          // The typed text stays in the input, so the user can send it there.
          await getConversations();
          const existingItem = findConversationItemByReceiverId(receiverId);
          if (existingItem) {
            await openConversation(existingItem);
          } else {
            showError('You already have a conversation with this user. Open it from the list.');
          }
        } else {
          showError(errorData.message || errorData.error || ('Failed to create conversation (HTTP ' + res.status + ')'));
        }
        return;
      }

      let data = await res.json();
      messageStream.dataset.conversationId = String(data.conversation_id);
      appendIncomingMessage(messageStream, {
        message_id: data.message_info.message_id,
        sender_info: {
          user_id: data.message_info.sender_id,
          display_name: currentUser.display_name || String(data.message_info.sender_display_name ?? ''),
          avatar_url: currentUser.avatar_url ?? null
        },
        conversation_id: data.conversation_id,
        message_type: data.message_info.message_type,
        message: data.message_info.content,
        created_at: data.message_info.created_at
      });
      messageStream.scrollTop = messageStream.scrollHeight;

      // Success: clear the input, forget the receiver, add the new conversation's row to the sidebar
      // from the response (same fields as GET /api/conversations, no list fetch)
      chatInput.value = '';
      delete document.getElementById('conversation-name').dataset.receiverId;
      const newItem = addConversationItem({
        conversation_id: data.conversation_id,
        conversation_type: data.conversation_type,
        receiver_id: data.receiver_id,
        display_name: data.receiver_display_name,
        conversation_img_url: data.conversation_img_url,
        latest_message: { content: data.message_info.content, created_at: data.message_info.created_at },
        unread_count: 0
      });
      setActiveConversationItem(newItem);
    } catch (error) {
      showError(error.message || 'Failed to create the conversation');
    }
    return;
  }
  if (!realTimeSocket.connected) {
    showError('Not connected to the server. Please try again.');
    return;
  }

  const payload = {
    sender_info: {
      user_id: currentUser.user_id,
      username: currentUser.username,
      display_name: currentUser.display_name,
      avatar_url: currentUser.avatar_url
    },
    conversation_id: conversationId,
    message: text
  };

  // No ack: the server saves the message, then emits 'receive_message' to every member,
  // this user included, and that handler draws it. A failure comes back as 'send_message_error'.
  realTimeSocket.emit('send_message', payload);
  chatInput.value = '';
  chatInput.focus();
};

sendButton.addEventListener('click', () => handleSubmitMessage(messageStreamElement));

chatInput.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter' || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  handleSubmitMessage(messageStreamElement);
});


// Every saved message arrives here: from the chat partner, and also our own (the server
// echoes it to all members, so each of this user's tabs shows it once it is saved).
realTimeSocket.on('receive_message', async (payload) => {
  const conversationId = String(payload.conversation_id);
  const isOwn = currentUser.user_id != null &&
    String(payload.sender_info?.user_id) === String(currentUser.user_id);
  const preview = { conversationId, message: payload.message, createAt: payload.created_at };

  // Our own message, or the open conversation: the row is updated, or drawn from
  // payload.conversation when this client does not have it yet. Never unread.
  const showWithoutUnread = () => {
    if (updateConversationPreview(preview) || !payload.conversation) return;
    addConversationItem({
      ...payload.conversation,
      latest_message: { content: payload.message, created_at: payload.created_at },
      unread_count: 0
    });
  };

  // The open conversation: show it in the stream AND update its sidebar preview
  if (conversationId === messageStreamElement.dataset.conversationId) {
    appendIncomingMessage(messageStreamElement, payload);
    if (isOwn) messageStreamElement.scrollTop = messageStreamElement.scrollHeight;
    showWithoutUnread();
    if (!isOwn) scheduleMarkRead();   // the user is looking at it: save "read up to this message"
    return;
  }

  // Another conversation, our own message (sent from another tab): preview only
  if (isOwn) {
    showWithoutUnread();
    return;
  }

  // Another conversation, from someone else: preview, time, bold, unread badge
  // (a conversation new to this client gets its row from payload.conversation)
  await handleNewMessageComing({ ...preview, conversation: payload.conversation });
});

// The server refused a message: show why, and give the text back if the composer is still empty
realTimeSocket.on('send_message_error', (payload) => {
  showError(payload?.message || 'The message could not be sent.');
  const isSameConversation =
    !payload?.conversation_id || payload.conversation_id === messageStreamElement.dataset.conversationId;
  if (payload?.text && isSameConversation && !chatInput.value) chatInput.value = payload.text;
});

/*
    {
        sender_info: {
            "user_id": 12,
            "username": "johnny",
            "display_name": "Johnny Smith",
            "avatar_url": null
        },
        "conversation_id": "conv123",
        "message": "Hello, this is a test message.",
        message_id: "1354263578912345678",
        created_at: "2026-11-19T05:20:00Z"
    }
*/


/*
# Conversations API

## Create a Direct Conversation

Create a new direct conversation between the logged-in user and another user.
The first message is created in the same request and cannot be empty.
The logged-in user is identified by the Flask session cookie.

### Endpoint

| Method | URL |
|--------|-----|
| `POST` | `{BASE_URL}/api/conversations/new-conversation?user_id={user_id}` |

Example base URL: `http://127.0.0.1:5000`

### Query Parameters

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `user_id` | integer | Yes | Must identify an existing user other than the logged-in user | User to start the conversation with |

Example:

```http
POST /api/conversations/new-conversation?user_id=7
```

### Request

#### Headers

| Header | Value | Required | Description |
|--------|-------|----------|-------------|
| `Content-Type` | `application/json` | Yes | Request body format |
| `Accept` | `application/json` | No | Expected response format |
| Cookie | Flask session cookie | Yes | Created by login; use `credentials: "include"` with `fetch` when needed |

#### Body

```json
{
  "message": "Hi Jane, how are you?"
}
```

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `message` | string | Yes | 1–2000 characters; not empty or whitespace-only | First message in the conversation |

JavaScript example:

```javascript
const response = await fetch(
  "/api/conversations/new-conversation?user_id=7",
  {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    body: JSON.stringify({ message: "Hi Jane, how are you?" })
  }
);

const data = await response.json();
```

### Successful Response

#### `201 Created`

The conversation and its first message were created successfully.

```json
{
  "conversation_id": 3,
  "conversation_type": "direct",
  "receiver_id": 7,
  "receiver_display_name": "Jane Doe",
  "conversation_img_url": "https://example.com/avatars/jane.png",
  "message_info": {
    "message_id": "123456789",
    "sender_id": 1,
    "sender_display_name": "John Doe",
    "message_type": "text",
    "content": "Hi Jane, how are you?",
    "created_at": "2026-11-22T18:05:05Z"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `conversation_id` | integer | New conversation ID; use it to load and send messages |
| `conversation_type` | string | Always `direct` for this endpoint |
| `receiver_id` | integer | ID of the other participant |
| `receiver_display_name` | string | Display name of the other participant |
| `conversation_img_url` | string \| null | Other participant's avatar URL, or `null` |
| `message_info` | object | The first message created with the conversation |

`message_info` contains `message_id`, `sender_id`, `sender_display_name`,
`message_type`, `content`, and `created_at`. The timestamp is an ISO 8601 UTC
string.

### Error Responses

All errors use this JSON shape:

```json
{
  "message": "error description"
}
```

| Status | Condition | Example `message` |
|--------|-----------|-------------------|
| `400` | Missing or invalid `user_id`, self-conversation, invalid JSON body, empty message, or message longer than 2000 characters | `"message must not be empty"` |
| `401` | No valid login session | `"401 Unauthorized"` |
| `404` | Target user does not exist or is blocked | `"User not found"` |
| `409` | A direct conversation between the users already exists | `"Conversation already exists"` |
| `500` | Unexpected server error | `"Internal server error"` |

Example:

```json
{
  "message": "Conversation already exists"
}
```

*/