import { showError } from "./error.js"

/* The sidebar conversation list ONLY: rows, rendering, preview, unread badge.
   Opening a conversation, loading messages, scrolling and marking read are in
   chat-area/messages-actions.js, which imports from this file (never the other way round). */

/*
<div class="conversation-item [is-active]" data-conversation-id="c1">

  <div class="conversation-avatar-wrap">
    <!-- one of these three, depending on the conversation -->
    <img class="conversation-avatar" alt="Marcus Vance" src="https://..." />        <!-- person with a photo -->
    <div class="conversation-initials">AM</div>                                      <!-- person without a photo -->
    <div class="conversation-channel-avatar">                                        <!-- group -->
      <span class="material-symbols-outlined">tag</span>
    </div>

    <span class="status-dot is-online"></span>      <!-- only if a status is set: is-online or is-idle -->
    <span class="unread-badge">2</span>             <!-- only if unread > 0 -->
  </div>

  <div class="conversation-body">
    <div class="conversation-top">
      <span class="conversation-name">Marcus Vance</span>
      <span class="conversation-time">09:50 AM</span>
    </div>
    <p class="conversation-preview">Attaching complete decking for afternoon...</p>
  </div>

</div>
*/
export const conversationList = document.getElementById('conversation-list');


/*
HTML Skeleton Reference:
    <div class="conversation-avatar-wrap">
      <!-- one of these three, depending on the conversation -->
      <img class="conversation-avatar" alt="Marcus Vance" src="https://..." />   <!-- person with a photo -->
      <div class="conversation-initials">AM</div>                                 <!-- person without a photo -->
      <div class="conversation-channel-avatar">                                   <!-- group -->
        <span class="material-symbols-outlined">tag</span>
      </div>

      <span class="status-dot is-online"></span>   <!-- only if a status is set: is-online or is-idle -->
      <span class="unread-badge">2</span>          <!-- only if unread > 0 -->
    </div>
*/
let createConversationAvatarWrap = ({avatarUrl, initials, isGroup, status, unreadCount}) => {
    const conversationAvatarWrap = document.createElement('div');
    conversationAvatarWrap.classList.add('conversation-avatar-wrap');

    if (avatarUrl) {
        const conversationAvatar = document.createElement('img');
        conversationAvatar.classList.add('conversation-avatar');
        conversationAvatar.alt = initials;
        conversationAvatar.src = avatarUrl;
        conversationAvatarWrap.appendChild(conversationAvatar);
    } else if (isGroup) {
        const conversationChannelAvatar = document.createElement('div');
        conversationChannelAvatar.classList.add('conversation-channel-avatar');
        const tagIcon = document.createElement('span');
        tagIcon.classList.add('material-symbols-outlined');
        tagIcon.textContent = 'tag';
        conversationChannelAvatar.appendChild(tagIcon);
        conversationAvatarWrap.appendChild(conversationChannelAvatar);
    } else if (initials) {
        const conversationInitials = document.createElement('div');
        conversationInitials.classList.add('conversation-initials');
        conversationInitials.textContent = initials;
        conversationAvatarWrap.appendChild(conversationInitials);
    }

    if (status) {
        const statusDot = document.createElement('span');
        statusDot.classList.add('status-dot', status);
        conversationAvatarWrap.appendChild(statusDot);
    }

    if (unreadCount > 0) {
        const unreadBadge = document.createElement('span');
        unreadBadge.classList.add('unread-badge');
        unreadBadge.textContent = unreadCount;
        conversationAvatarWrap.appendChild(unreadBadge);
    }

    return conversationAvatarWrap;
}

/*
HTML Skeleton Reference:
      <div class="conversation-body">
        <div class="conversation-top">
          <span class="conversation-name">Marcus Vance</span>
          <span class="conversation-time">09:50 AM</span>
        </div>
        <p class="conversation-preview">Attaching complete decking for afternoon...</p>
      </div>
*/
let createConversationBody = ({name, time, preview}) => {
    const conversationBody = document.createElement('div');
    conversationBody.classList.add('conversation-body');
    const conversationTop = document.createElement('div');
    conversationTop.classList.add('conversation-top');
    const conversationName = document.createElement('span');
    conversationName.classList.add('conversation-name');
    conversationName.textContent = name;
    const conversationTime = document.createElement('span');
    conversationTime.classList.add('conversation-time');
    conversationTime.textContent = time;
    const conversationPreview = document.createElement('p');
    conversationPreview.classList.add('conversation-preview');
    conversationPreview.textContent = preview;
    conversationTop.appendChild(conversationName);
    conversationTop.appendChild(conversationTime);
    conversationBody.appendChild(conversationTop);
    conversationBody.appendChild(conversationPreview);
    return conversationBody;
}


/*
HTML Skeleton Reference:
<div class="conversation-item [is-active]" data-conversation-id="c1">
  <div class="conversation-avatar-wrap">...</div>
  <div class="conversation-body">...</div>
</div>
*/
export function createConversationItem({
    id,
    avatarUrl,
    initials,
    isGroup,
    status,
    unreadCount,
    name,
    time,
    preview,
    receiverId
}) {
    if (!id || !name) {
        showError('Missing required conversation properties: id and name are required.');
        return null;
    }
    
    const conversationItem = document.createElement('div');
    conversationItem.classList.add('conversation-item');
    if (id) {
        conversationItem.setAttribute('data-conversation-id', id);
    }
    // The other person of a direct conversation (null for a group). Used to find the row by user.
    if (receiverId !== undefined && receiverId !== null) {
        conversationItem.dataset.receiverId = String(receiverId);
    }

    const conversationAvatarWrap = createConversationAvatarWrap({avatarUrl, initials, isGroup, status, unreadCount});
    conversationItem.appendChild(conversationAvatarWrap);

    const conversationBody = createConversationBody({name, time, preview});
    conversationItem.appendChild(conversationBody);
    if (unreadCount > 0) {
        conversationItem.classList.add('has-unread');
    }

    return conversationItem;
}

function initials(name = '') {
    const parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return '?';
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// Module level: renderConversations and handleNewMessageComing both need it
const formatConversationTime = (iso) =>
    iso ? new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

function renderConversations(conversations) {
    if (!Array.isArray(conversations)) {
        showError('Invalid conversations data: expected an array.');
        return;
    }

    const activeConversationId = conversationList
        .querySelector('.conversation-item.is-active')?.dataset.conversationId;
    conversationList.replaceChildren();
    if (conversations.length === 0) {
        const emptyState = document.createElement('p');
        emptyState.classList.add('conversation-empty');
        emptyState.textContent = 'No conversations yet.';
        conversationList.appendChild(emptyState);
        return;
    }

    conversations.forEach(conversation => {
        const conversationItem = createConversationItem(toConversationItemInput(conversation));
        if (conversationItem) {
            if (conversationItem.dataset.conversationId === activeConversationId) {
                conversationItem.classList.add('is-active');
            }
            conversationList.appendChild(conversationItem);
        }
    });
}

// One item of GET /api/conversations (or the `conversation` of a socket payload) -> createConversationItem() input
const toConversationItemInput = (conversation) => ({
    id: String(conversation.conversation_id),
    avatarUrl: conversation.conversation_img_url,
    initials: initials(conversation.display_name),
    isGroup: conversation.conversation_type === 'group',
    receiverId: conversation.receiver_id,
    unreadCount: Number(conversation.unread_count) || 0,
    name: conversation.display_name,
    time: formatConversationTime(conversation.latest_message?.created_at),
    preview: conversation.latest_message?.content ||
        (conversation.conversation_type === 'group' ? 'Group conversation' : 'No messages yet')
});

const findConversationItem = (conversationId) =>
    conversationList.querySelector(
        '.conversation-item[data-conversation-id="' + CSS.escape(String(conversationId)) + '"]'
    );

// Adds ONE row at the top of the list, without fetching the list again.
// conversation: { conversation_id, conversation_type, receiver_id, display_name,
//                 conversation_img_url, [latest_message: { content, created_at }], [unread_count] }
// (same shape as GET /api/conversations; socket payloads carry it as `conversation`)
// Returns the row. If the row exists already, nothing is added and that row is returned.
export function addConversationItem(conversation) {
    const existingItem = findConversationItem(conversation.conversation_id);
    if (existingItem) return existingItem;

    const conversationItem = createConversationItem(toConversationItemInput(conversation));
    if (!conversationItem) return null;

    conversationList.querySelector('.conversation-empty')?.remove();   // "No conversations yet."
    conversationList.prepend(conversationItem);
    return conversationItem;
}



// Updates the preview and the time of a row and moves it to the top. No unread badge.
// Used for your own sent message (messages-actions.js) and, through handleNewMessageComing, for incoming ones.
// Returns false when the row is not in the list.
export function updateConversationPreview({ conversationId, message, createAt }) {
    const item = Array.from(conversationList.children).find(
        (child) => child.dataset.conversationId === conversationId
    );
    if (!item) return false;

    item.querySelector('.conversation-preview').textContent = message;
    item.querySelector('.conversation-time').textContent = formatConversationTime(createAt);
    conversationList.prepend(item);   // newest conversation on top
    return true;
}

// Replaces the preview and the time of a row WITHOUT moving it (a deleted message is not
// new activity). message = null: the conversation has no message left.
// Returns false when the row is not in the list.
export function setConversationPreview({ conversationId, message, createAt }) {
    const item = findConversationItem(conversationId);
    if (!item) return false;

    item.querySelector('.conversation-preview').textContent = message ?? 'No messages yet';
    item.querySelector('.conversation-time').textContent = message ? formatConversationTime(createAt) : '';
    return true;
}

// A message from someone else for a conversation that is not open:
// update the row, make it bold and add 1 to its unread badge.
// conversation: the `conversation` of the socket payload, used to draw the row when the
// conversation is new to this client (first message of a direct chat, a new group).
export async function handleNewMessageComing({ conversationId, message, createAt, conversation }) {
    const isUpdated = updateConversationPreview({ conversationId, message, createAt });
    if (!isUpdated) {
        if (!conversation) {
            await getConversations();   // old server payload without `conversation`: only way left
            return;
        }
        // New conversation: draw its row from the payload, already bold with 1 unread
        addConversationItem({
            ...conversation,
            latest_message: { content: message, created_at: createAt },
            unread_count: 1
        });
        return;
    }

    const item = findConversationItem(conversationId);
    item.classList.add('has-unread');

    let unreadBadge = item.querySelector('.unread-badge');
    if (!unreadBadge) {
        unreadBadge = document.createElement('span');
        unreadBadge.classList.add('unread-badge');
        unreadBadge.textContent = '0';
        item.querySelector('.conversation-avatar-wrap').appendChild(unreadBadge);
    }
    unreadBadge.textContent = Number(unreadBadge.textContent) + 1;
}

// handle get conversations from server
export async function getConversations() {
    try {
        const response = await fetch('/api/conversations',
            {
                method: 'GET',
                credentials: 'include'
            }
        );
        const body = await response.json();
        if (!response.ok) {
            showError(body?.message || 'Failed to fetch conversations');
            return false;
        }
        renderConversations(body);
        return true;
    } catch (error) {
        showError('Failed to fetch conversations');
        return false;
    }
}

/*
Sidebar row of the direct conversation with a user, or null.
HTML Skeleton Reference (what is matched):
<div class="conversation-item" data-conversation-id="3" data-receiver-id="7">...</div>
*/
export const findConversationItemByReceiverId = (userId) =>
    conversationList.querySelector(
        '.conversation-item[data-receiver-id="' + CSS.escape(String(userId)) + '"]'
    );

// Highlights one row. item = null removes the highlight from every row.
export const setActiveConversationItem = (item) => {
    const previousItem = conversationList.querySelector('.conversation-item.is-active');
    if (previousItem && previousItem !== item) previousItem.classList.remove('is-active');
    if (item) item.classList.add('is-active');
};

// The conversation was read: remove the bold state and the unread badge of its row
export const clearConversationUnread = (conversationId) => {
    const item = conversationList.querySelector(
        '.conversation-item[data-conversation-id="' + CSS.escape(String(conversationId)) + '"]'
    );
    if (!item) return;
    item.classList.remove('has-unread');
    const unreadBadge = item.querySelector('.unread-badge');
    if (unreadBadge) unreadBadge.remove();
};

// Name shown in a row (used as the chat title)
export const getConversationName = (item) =>
    item.querySelector('.conversation-name').textContent;

/*
### Endpoint
 
| Method | URL |
|--------|-----|
| `GET` | `{BASE_URL}/api/conversations` |
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
    },
    "unread_count": 3
  },
  {
    "conversation_id": 2,
    "conversation_type": "group",
    "receiver_id": null,
    "display_name": "Project Team",
    "conversation_img_url": null,
    "latest_message": null,
    "unread_count": 0
  }
]


@socketio.on('send_message')
def on_message(data):
    """
    data: 
    {
        sender_info: {
            "user_id": 12,
            "username": "johnny",
            "display_name": "Johnny Smith",
            "avatar_url": null
        },
        "conversation_id": "conv123",
        "message": "Hello, this is a test message."
    }

    response: 
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