import { createDateDivider, createMessage } from './messages-stream.js';


const currentUser = JSON.parse(
  localStorage.getItem('user') || '{}'
);
/* Turns server data (REST page or Socket.IO event) into createMessage() input and
   puts it into #message-stream. Load after message-stream.js.
   There is no network code here: your API / socket code calls these functions with
   the data it receives. */

/* ---------- 1. Normalize: two server shapes -> one shape ---------- */

// REST item: { message_id, sender_id, sender_display_name, message_type, content, created_at }
const normalizeRestMessage = (raw) => ({
  id: raw.message_id,
  senderId: raw.sender_id,
  author: raw.sender_display_name,
  avatarUrl: null,
  type: raw.message_type,
  content: raw.content,
  createdAt: raw.created_at
});

// Socket payload: { sender_info: { user_id, display_name, avatar_url, ... },
//                   conversation_id, message, message_id, created_at, [message_type] }
const normalizeSocketMessage = (raw) => ({
  id: raw.message_id,
  senderId: raw.sender_info.user_id,
  author: raw.sender_info.display_name,
  avatarUrl: raw.sender_info.avatar_url,
  type: raw.message_type || 'text',
  content: raw.message,
  createdAt: raw.created_at
});

/* ---------- 2. Decide what the content is: text, image or file ---------- */

const FILE_ICONS = {
  pdf: 'picture_as_pdf', doc: 'description', docx: 'description',
  xls: 'table_chart', xlsx: 'table_chart', csv: 'table_chart',
  ppt: 'slideshow', pptx: 'slideshow', txt: 'article',
  zip: 'folder_zip', rar: 'folder_zip', mp3: 'audio_file', mp4: 'video_file'
};
const DEFAULT_FILE_ICON = 'draft';
const IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'];

// The whole content must be one http(s) URL, otherwise null
const parseHttpUrl = (text) => {
  const trimmed = text.trim();
  if (!trimmed || /\s/.test(trimmed)) return null;
  try {
    const url = new URL(trimmed);
    return url.protocol === 'http:' || url.protocol === 'https:' ? url : null;
  } catch (error) {
    return null;
  }
};

const getFileName = (url) => {
  const last = url.pathname.split('/').pop();
  try {
    return decodeURIComponent(last) || url.hostname;
  } catch (error) {
    return last || url.hostname;
  }
};

const getExtension = (url) => {
  const name = url.pathname.split('/').pop();
  const dot = name.lastIndexOf('.');
  return dot === -1 ? '' : name.slice(dot + 1).toLowerCase();
};

// message_type from the server wins. Today it is always 'text', so for 'text'
// a single URL is classified by its extension. A link without a known
// extension stays plain text.
const detectContent = ({ type, content }) => {
  const url = parseHttpUrl(content);
  if (!url) return { kind: 'text' };

  const extension = getExtension(url);
  if (type === 'image') return { kind: 'image', url, extension };
  if (type === 'file') return { kind: 'file', url, extension };
  if (IMAGE_EXTENSIONS.includes(extension)) return { kind: 'image', url, extension };
  if (FILE_ICONS[extension]) return { kind: 'file', url, extension };
  return { kind: 'text' };
};

/* ---------- 3. Formatting helpers ---------- */

const getInitials = (name) => {
  const words = String(name ?? '').trim().split(/\s+/).filter(Boolean);
  if (!words.length) return '?';
  const first = words[0][0];
  const last = words.length > 1 ? words[words.length - 1][0] : '';
  return (first + last).toUpperCase();
};

const formatTime = (iso) =>
  new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

// Local calendar day, e.g. '2026-11-16'. Accepts an ISO string or a Date.
const getDayKey = (value) => {
  const date = new Date(value);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return date.getFullYear() + '-' + month + '-' + day;
};

const formatDayLabel = (iso) => {
  const full = new Date(iso).toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' });
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);

  if (getDayKey(iso) === getDayKey(new Date())) return 'Today, ' + full;
  if (getDayKey(iso) === getDayKey(yesterday)) return 'Yesterday, ' + full;
  return full;
};

/* ---------- 4. Normalized message -> createMessage() input ---------- */

// Role and status are not sent by the server, so they are left out
// (the header has no badge and the avatar has no status dot).
const toMessageInput = (message, { isNew = false } = {}) => {
  const input = {
    id: message.id,
    author: message.author,
    avatarUrl: message.avatarUrl || undefined,
    initials: getInitials(message.author),
    time: formatTime(message.createdAt),
    isNew,
    isOwn: currentUser.user_id != null && String(message.senderId) === String(currentUser.user_id)
  };

  const content = detectContent(message);
  if (content.kind === 'text') {
    return { ...input, parts: [{ type: 'text', value: message.content }] };
  }

  const fileName = getFileName(content.url);
  const label = content.extension.toUpperCase();

  if (content.kind === 'image') {
    return {
      ...input,
      parts: [],
      attachment: {
        kind: 'image',
        src: content.url.href,
        alt: fileName,
        fileName,
        meta: label || 'Image'
      }
    };
  }

  return {
    ...input,
    parts: [],
    attachment: {
      kind: 'file',
      icon: FILE_ICONS[content.extension] || DEFAULT_FILE_ICON,
      fileName,
      meta: label ? label + ' file' : 'File'
    }
  };
};

/* ---------- 5. Put messages into #message-stream ---------- */

const createDayDivider = (iso) => {
  const divider = createDateDivider({ label: formatDayLabel(iso) });
  divider.dataset.day = getDayKey(iso);
  return divider;
};

/*
HTML Skeleton Reference (nodes returned, oldest first):
<div class="date-divider" data-day="2026-11-16">...</div>   <!-- once per day -->
<div class="message" data-message-id="1234577">...</div>
<div class="message" data-message-id="1234578">...</div>
*/
const buildStreamNodes = (messages) => {
  const nodes = [];
  let lastDay = null;

  messages.forEach((message) => {
    const day = getDayKey(message.createdAt);
    if (day !== lastDay) {
      nodes.push(createDayDivider(message.createdAt));
      lastDay = day;
    }
    nodes.push(createMessage(toMessageInput(message)));
  });

  return nodes;
};

/*
HTML Skeleton Reference (content of #message-stream):
<div class="date-divider">...</div>
<div class="message">...</div>   <!-- one per message, oldest at the top -->
*/
// Endpoint: GET {BASE_URL}/api/messages?conversation_id={conversation_id}&limit={limit}
// First page (no `before`), newest message last. Call it when a conversation is opened.
// messagesStream: document.getElementById('message-stream')
const renderMessageHistory = (messageStream, rawMessages) => {
  // The REST array is newest first, the screen shows oldest first
  const ordered = rawMessages.map(normalizeRestMessage).reverse();
  messageStream.replaceChildren(...buildStreamNodes(ordered));
  messageStream.scrollTop = messageStream.scrollHeight;
};

// Endpoint: none (reads the screen). Its result is the `before` value for
// GET {BASE_URL}/api/messages?conversation_id={conversation_id}&before={getOldestMessageId()}&limit={limit}
// messagesStream: document.getElementById('message-stream')
const getOldestMessageId = (messageStream) => {
  const oldest = messageStream.querySelector('.message');
  return oldest ? oldest.dataset.messageId : null;
};

// GET {BASE_URL}/api/messages?conversation_id={conversation_id}&before={message_id}&limit={limit}
// Older page. `message_id` comes from getOldestMessageId(). If the array has fewer items
// than `limit`, there are no older messages left.
// Used when user scrolls up.
// messagesStream: document.getElementById('message-stream')
const prependOlderMessages = (messageStream, rawMessages) => {
  if (!rawMessages.length) return;
  const ordered = rawMessages.map(normalizeRestMessage).reverse();

  // The current top divider is repeated when both pages share a day
  const newestOlderDay = getDayKey(ordered[ordered.length - 1].createdAt);
  const firstNode = messageStream.firstElementChild;
  if (firstNode && firstNode.classList.contains('date-divider') && firstNode.dataset.day === newestOlderDay) {
    firstNode.remove();
  }

  const heightBefore = messageStream.scrollHeight;
  messageStream.prepend(...buildStreamNodes(ordered));
  messageStream.scrollTop += messageStream.scrollHeight - heightBefore;
};

/*
HTML Skeleton Reference (appended at the end of #message-stream):
<div class="date-divider">...</div>            <!-- only when the day changed -->
<div class="message message-new">...</div>
*/
// Endpoint: Socket.IO event 'receive_message' (server emits it after a client's 'send_message')
// Payload: { sender_info, conversation_id, message, message_id, created_at }
// Your own message arrives through the same event: the server echoes it to the sender's room too.
// messagesStream: document.getElementById('message-stream')
const appendIncomingMessage = (messageStream, payload) => {
  const message = normalizeSocketMessage(payload);
  const nodes = [];

  const dividers = messageStream.querySelectorAll('.date-divider');
  const lastDivider = dividers[dividers.length - 1];
  if (!lastDivider || lastDivider.dataset.day !== getDayKey(message.createdAt)) {
    nodes.push(createDayDivider(message.createdAt));
  }
  nodes.push(createMessage(toMessageInput(message, { isNew: true })));

  // Only follow the new message if the user is already near the bottom
  const distanceFromBottom =
    messageStream.scrollHeight - messageStream.scrollTop - messageStream.clientHeight;
  messageStream.append(...nodes);
  if (distanceFromBottom < 80) messageStream.scrollTop = messageStream.scrollHeight;
};


export {
  renderMessageHistory,
  getOldestMessageId,
  prependOlderMessages,
  appendIncomingMessage
};