await (async function () {
  'use strict';

  /* =====================================================
     Hypothetical data
     Everything the UI shows lives in the const objects below.
     Nothing in this file talks to a server.
     ===================================================== */

  const AVATARS = {
    marcus: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBsRdp1e4FvLW2W9mqEPViBlDLzuFs6XVNI2J9PH5fB3Beat8BeYQo6_vUxN1fJaud89w2pSEBSCRg_xqd-73yq2P8rnu9N0WUq3mOMIYYsbKE0nDftoTLPNbZsNcARX4g3a74RVKV0FB7ZjauKXaRiNirIIfdMjFduDuAef_EeIO1Cnt02GF22af-8TzP4UpncHhW-R-fH_V4KznxjV0_6LKHmmD8XNk1GonoK__tcZIMRpc4OzSGGeA',
    marcusAlt: 'https://lh3.googleusercontent.com/aida-public/AB6AXuChblbCei76PhCZuYGbibw4cynV_Sf-dbWcPJmDvYYjDA9nNkAwlkyfR654Q0yvXEjdT2FUQBMaBKU7HTn9eXhPBgLUerZehtY4l5As6_SbLAjDQFg5yRZaOOKqB5-tKqgAJ-bLVpzntEktGSDmw7NC25ptZyMeQZfDy7od-u-Yn1LA073vYqzSqokEVNiUf0XywBwfCGKw76_krpRZFuIu8_UPnVYtNcfHCWYAWrlYWo9KN9Fevgc3Cg',
    elena: 'https://lh3.googleusercontent.com/aida-public/AB6AXuC56DWjPONVX8EdJesAI5DaX9Kk8lNQP_u94LtqnC2n6MmTMsm3kq7YxAb3fhxoiA4SwUZ2seUGcSWOGbEnAjevT_zl_XRXgBOinNBB_WI1xVFQRrFijyA2gwXnzCaviJvqJgdnIWXE0QFttTFR-x71xVgR8gVlMt-yUljRKZ2CNSNt9-gW_aYvDlcxvJqtVMuKcdbEP-PFyuvsuRJCriJ_mbzpfUXv3BSJkWy1zWJT0bivo1SLOMxA3w',
    wireframe: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCMIRFpDsu4u_qXvo7a93COqr_Dm-grJjLLaJYjav5u5ulaSK-9qe34dt_SJMlgJJJon5bSALBfQcQMo3_H8y6bAOYdU3WS3lxANAUeVlhT1df1FiD7nIK_OddUvYt1yo_Bxr0uF-jrY9zLj3uEGKFFJYtQlHCDTeLYski-_bmfwIHGZB06fktSg4PjR5KSt0I_O7cSYVuMxu1Qcppv9Hg1wgxayY4KVsCc6B4EAhKoR-2N1_neEVlUQQ'
  };

  const currentUser = {
    id: 'u0',
    name: 'Alex Mercer',
    role: { label: 'Lead', variant: 'lead' }
  };

  // People that can be found with "search people" / "Add friend"
  const directory = [
    { id: 'u1', name: 'Priya Nair', handle: '@priya' },
    { id: 'u2', name: 'Tom Becker', handle: '@tbecker' },
    { id: 'u3', name: 'Sofia Lindqvist', handle: '@sofia' },
    { id: 'u4', name: 'Daniel Okafor', handle: '@dokafor' },
    { id: 'u5', name: 'Mina Park', handle: '@mina' },
    { id: 'u6', name: 'Marcus Vance', handle: '@mvance' },
    { id: 'u7', name: 'Elena Rostova', handle: '@elena' }
  ];

  // Sidebar entries. kind: 'person' | 'group'. status: 'online' | 'idle' | undefined
  const conversations = [
    {
      id: 'c1',
      kind: 'person',
      name: 'Marcus Vance',
      time: '09:50 AM',
      preview: 'Attaching complete decking for afternoon...',
      avatarUrl: AVATARS.marcus,
      status: 'online',
      unread: 0
    },
    {
      id: 'c2',
      kind: 'person',
      name: 'Elena Rostova',
      time: '09:44 AM',
      preview: 'I wrote a lightweight subscriber to monitor...',
      avatarUrl: AVATARS.elena,
      status: 'online',
      unread: 2
    },
    {
      id: 'c3',
      kind: 'group',
      name: 'general-product-core',
      time: 'Yesterday',
      preview: "Tanya: Looks great! Let's ship.",
      status: 'idle',
      unread: 0
    },
    {
      id: 'c4',
      kind: 'person',
      name: 'Alex Mercer',
      time: '10:02 AM',
      preview: "Here's the spatial bounding matrix showing...",
      status: 'online',
      unread: 0
    }
  ];

  // Messages of the open conversation.
  // text: array of parts ({ type: 'text' | 'code', value }).
  // attachment: null | { kind: 'code' | 'file' | 'image', ... }
  const messageThread = {
    dateLabel: 'Today, October 24, 2024',
    messages: [
      {
        id: 'm1',
        author: 'Marcus Vance',
        avatarUrl: AVATARS.marcus,
        status: 'online',
        role: { label: 'Staff Eng', variant: 'staff' },
        time: '09:41 AM',
        text: [
          { type: 'text', value: 'Morning team! Updated token scales are merged into ' },
          { type: 'code', value: 'main' },
          {
            type: 'text',
            value: ". Please verify high-contrast typography mappings follow revised design specs before today's sync."
          }
        ],
        attachment: null
      },
      {
        id: 'm2',
        author: 'Elena Rostova',
        avatarUrl: AVATARS.elena,
        status: 'online',
        role: { label: 'Core Systems', variant: 'core' },
        time: '09:44 AM',
        text: [
          {
            type: 'text',
            value: 'I wrote a lightweight subscriber to monitor color mode mismatches on client mounts:'
          }
        ],
        attachment: {
          kind: 'code',
          fileName: 'tokenObserver.ts',
          // type: 'keyword' | 'function' | 'string' | 'muted' | undefined (plain text)
          tokens: [
            { text: 'export const', type: 'keyword' },
            { text: ' ' },
            { text: 'watchContrastTokens', type: 'function' },
            { text: ' = (theme: ThemeMode) => {\n  ' },
            { text: 'const', type: 'muted' },
            { text: ' root = document.documentElement;\n  ' },
            { text: 'const', type: 'keyword' },
            { text: ' required = [' },
            { text: "'--on-surface'", type: 'string' },
            { text: ', ' },
            { text: "'--surface-container'", type: 'string' },
            { text: '];\n\n  ' },
            { text: 'return', type: 'keyword' },
            { text: ' required.every(key => {\n    ' },
            { text: 'return', type: 'keyword' },
            { text: ' getComputedStyle(root).getPropertyValue(key).length > 0;\n  });\n};' }
          ]
        }
      },
      {
        id: 'm3',
        author: 'Marcus Vance',
        avatarUrl: AVATARS.marcusAlt,
        status: 'online',
        role: { label: 'Staff Eng', variant: 'staff' },
        time: '09:50 AM',
        text: [
          {
            type: 'text',
            value: 'Attaching the complete presentation decking for the afternoon governance panel:'
          }
        ],
        attachment: {
          kind: 'file',
          icon: 'picture_as_pdf',
          name: 'Q3_Design_Review_v2.pdf',
          verifiedTitle: 'Verified Architecture Document',
          meta: '4.2 MB • PDF Document'
        }
      },
      {
        id: 'm4',
        author: 'Alex Mercer',
        status: 'online',
        role: { label: 'Lead', variant: 'lead' },
        time: '10:02 AM',
        text: [
          {
            type: 'text',
            value: "Here's the spatial bounding matrix showing layout rules across responsive breakpoints:"
          }
        ],
        attachment: {
          kind: 'image',
          alt: 'Interface design wireframe diagram',
          src: AVATARS.wireframe,
          fileName: 'thread_spec_v04.png',
          meta: '2560 × 1440 • 840 KB'
        }
      }
    ]
  };

  // Friend requests and group invites shown in the bell dialog
  const notifications = [
    { id: 'n1', type: 'friend', name: 'Priya Nair', text: 'sent you a friend request', time: '5m ago' },
    { id: 'n2', type: 'group', name: 'Tom Becker', group: 'design-systems', text: 'invited you to join', time: '1h ago' },
    { id: 'n3', type: 'friend', name: 'Sofia Lindqvist', text: 'sent you a friend request', time: 'Yesterday' }
  ];

  // UI state
  const requestedUserIds = new Set(); // people the user pressed "Add friend" for
  let activeConversationId = 'c1';
  let idCounter = 100;

  /* =====================================================
     Page elements
     ===================================================== */

  const $ = function (id) { return document.getElementById(id); };

  const conversationList = document.querySelector('.conversation-list');
  const topbarRight = document.querySelector('.topbar-right');
  const messageStream = $('message-stream');
  const chatInput = $('chat-input');
  const sendBtn = $('send-btn');

  const searchInput = $('sidebar-search-input');
  const searchClear = $('sidebar-search-clear');

  const addFriendInput = $('add-friend-input');
  const addFriendResults = $('add-friend-results');

  const groupNameInput = $('group-name-input');
  const groupMembers = $('group-members');
  const groupSubmit = $('create-group-submit');

  const notifBadge = $('notif-badge');
  const notificationList = $('notification-list');

  const toast = $('toast');

  /* =====================================================
     Small helpers
     ===================================================== */

  function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  }

  function initials(name) {
    return name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map(function (word) { return word[0].toUpperCase(); })
      .join('');
  }

  function generateId(prefix) {
    idCounter += 1;
    return prefix + idCounter;
  }

  function findConversation(id) {
    return conversations.find(function (conversation) { return conversation.id === id; });
  }

  function findUser(id) {
    return directory.find(function (user) { return user.id === id; });
  }

  function searchUsers(query) {
    const q = query.toLowerCase();
    return directory.filter(function (user) {
      return user.name.toLowerCase().includes(q) || user.handle.toLowerCase().includes(q);
    });
  }

  function isFriend(user) {
    return conversations.some(function (conversation) {
      return conversation.kind === 'person' &&
        conversation.name.toLowerCase() === user.name.toLowerCase();
    });
  }

  let toastTimer = null;

  function showToast(text) {
    toast.textContent = text;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.hidden = true; }, 2500);
  }

  /* =====================================================
     DOM factories: shared pieces
     ===================================================== */

  /*
  HTML Skeleton Reference:
  <span class="material-symbols-outlined [extra-class]">icon_name</span>
  */
  function createIcon(name, extraClass) {
    return createElement(
      'span',
      'material-symbols-outlined' + (extraClass ? ' ' + extraClass : ''),
      name
    );
  }


  /* =====================================================
     Error notifications (call showError('short message'))
     ===================================================== */

  const ERROR_DURATION_MS = 5000;
  const errorStack = $('error-stack');
  const errorTimers = new Map(); // error id -> auto-dismiss timer

  /*
  HTML Skeleton Reference:
  <div class="error-toast" role="alert" data-error-id="e101">
    <span class="material-symbols-outlined">error</span>
    <p class="error-toast-text">Message</p>
    <button class="error-toast-close" type="button" title="Dismiss" data-error-close>
      <span class="material-symbols-outlined">close</span>
    </button>
  </div>
  */
  function createErrorToast(id, message) {
    const closeButton = createElement('button', 'error-toast-close');
    closeButton.type = 'button';
    closeButton.setAttribute('title', 'Dismiss');
    closeButton.dataset.errorClose = '';
    closeButton.appendChild(createIcon('close'));

    const toastElement = createElement('div', 'error-toast');
    toastElement.setAttribute('role', 'alert');
    toastElement.dataset.errorId = id;
    toastElement.appendChild(createIcon('error'));
    toastElement.appendChild(createElement('p', 'error-toast-text', message));
    toastElement.appendChild(closeButton);
    return toastElement;
  }

  function dismissError(id) {
    clearTimeout(errorTimers.get(id));
    errorTimers.delete(id);
    const element = errorStack.querySelector('[data-error-id="' + id + '"]');
    if (element) element.remove();
  }

  function showError(message) {
    const id = generateId('e');
    errorStack.appendChild(createErrorToast(id, message));
    errorTimers.set(id, setTimeout(function () { dismissError(id); }, ERROR_DURATION_MS));
  }

  // One click listener for every error card: the card says who it is via data-error-id
  errorStack.addEventListener('click', function (event) {
    if (!event.target.closest('[data-error-close]')) return;
    dismissError(event.target.closest('[data-error-id]').dataset.errorId);
  });

  /*
  HTML Skeleton Reference:
  <p class="modal-hint">Hint text</p>
  */
  function createHint(text) {
    return createElement('p', 'modal-hint', text);
  }

  /* =====================================================
     DOM factories: sidebar conversations
     ===================================================== */

  /*
  HTML Skeleton Reference:
  <div class="conversation-avatar-wrap">
    <!-- person with a photo -->
    <img class="conversation-avatar" alt="Marcus Vance" src="https://..." />
    <!-- person without a photo -->
    <div class="conversation-initials">AM</div>
    <!-- group -->
    <div class="conversation-channel-avatar">
      <span class="material-symbols-outlined">tag</span>
    </div>
    <!-- only when a status is known -->
    <span class="status-dot is-online"></span>   <!-- or is-idle -->
    <!-- only when unread > 0 -->
    <span class="unread-badge">2</span>
  </div>
  */
  function createConversationAvatar(conversation) {
    const wrap = createElement('div', 'conversation-avatar-wrap');

    if (conversation.kind === 'group') {
      const channelAvatar = createElement('div', 'conversation-channel-avatar');
      channelAvatar.appendChild(createIcon('tag'));
      wrap.appendChild(channelAvatar);
    } else if (conversation.avatarUrl) {
      const photo = createElement('img', 'conversation-avatar');
      photo.setAttribute('alt', conversation.name);
      photo.setAttribute('src', conversation.avatarUrl);
      wrap.appendChild(photo);
    } else {
      wrap.appendChild(createElement('div', 'conversation-initials', initials(conversation.name)));
    }

    if (conversation.status) {
      wrap.appendChild(createElement('span', 'status-dot is-' + conversation.status));
    }
    if (conversation.unread > 0) {
      wrap.appendChild(createElement('span', 'unread-badge', String(conversation.unread)));
    }
    return wrap;
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
  function createConversationBody(conversation) {
    const top = createElement('div', 'conversation-top');
    top.appendChild(createElement('span', 'conversation-name', conversation.name));
    top.appendChild(createElement('span', 'conversation-time', conversation.time));

    const body = createElement('div', 'conversation-body');
    body.appendChild(top);
    body.appendChild(createElement('p', 'conversation-preview', conversation.preview));
    return body;
  }

  /*
  HTML Skeleton Reference:
  <div class="conversation-item [is-active]" data-conversation-id="c1">
    <div class="conversation-avatar-wrap">...</div>
    <div class="conversation-body">...</div>
  </div>
  */
  function createConversationItem(conversation) {
    const item = createElement('div', 'conversation-item');
    item.dataset.conversationId = conversation.id;
    if (conversation.id === activeConversationId) item.classList.add('is-active');

    item.appendChild(createConversationAvatar(conversation));
    item.appendChild(createConversationBody(conversation));
    return item;
  }

  /* =====================================================
     DOM factories: sidebar search results and "Add friend"
     ===================================================== */

  /*
  HTML Skeleton Reference:
  <div class="search-section">                      <!-- created once, refilled on every search -->
    <div class="search-section-title">Add friend</div>
    <div class="user-row">...</div>                  <!-- one createUserRow() per person -->
  </div>
  */
  function createSearchSection() {
    const section = createElement('div', 'search-section');
    section.hidden = true;
    return section;
  }

  /*
  HTML Skeleton Reference:
  <div class="search-section-title">Add friend</div>
  */
  function createSearchSectionTitle(text) {
    return createElement('div', 'search-section-title', text);
  }

  /*
  HTML Skeleton Reference:
  <p class="search-empty">No people or groups found</p>
  */
  function createSearchEmpty() {
    const empty = createElement('p', 'search-empty', 'No people or groups found');
    empty.hidden = true;
    return empty;
  }

  function getFriendshipState(user) {
    if (isFriend(user)) return 'friends';
    if (requestedUserIds.has(user.id)) return 'requested';
    return 'none';
  }

  /*
  HTML Skeleton Reference:
  <button class="btn btn-primary" type="button" data-user-id="u1">Add friend</button>
  <!-- already requested / already a friend -->
  <button class="btn btn-secondary" type="button" data-user-id="u1" disabled>Requested | Friends</button>
  */
  function createAddFriendButton(user) {
    const state = getFriendshipState(user);
    const button = createElement('button', 'btn btn-primary', 'Add friend');
    button.type = 'button';
    button.dataset.userId = user.id;

    if (state !== 'none') {
      button.className = 'btn btn-secondary';
      button.textContent = state === 'friends' ? 'Friends' : 'Requested';
      button.disabled = true;
    }
    return button;
  }

  /*
  HTML Skeleton Reference:
  <div class="user-row">
    <div class="user-row-avatar">PN</div>
    <div class="user-row-info">
      <span class="user-row-name">Priya Nair</span>
      <span class="user-row-sub">@priya</span>
    </div>
    <button class="btn btn-primary" type="button" data-user-id="u1">Add friend</button>
  </div>
  */
  function createUserRow(user) {
    const info = createElement('div', 'user-row-info');
    info.appendChild(createElement('span', 'user-row-name', user.name));
    info.appendChild(createElement('span', 'user-row-sub', user.handle));

    const row = createElement('div', 'user-row');
    row.appendChild(createElement('div', 'user-row-avatar', initials(user.name)));
    row.appendChild(info);
    row.appendChild(createAddFriendButton(user));
    return row;
  }

  /* =====================================================
     DOM factories: create-group members
     ===================================================== */

  /*
  HTML Skeleton Reference:
  <label class="user-row member-row">
    <div class="user-row-avatar">MV</div>
    <div class="user-row-info">
      <span class="user-row-name">Marcus Vance</span>
    </div>
    <input type="checkbox" value="Marcus Vance" />
  </label>
  */
  function createMemberRow(name) {
    const info = createElement('div', 'user-row-info');
    info.appendChild(createElement('span', 'user-row-name', name));

    const checkbox = createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = name;

    const row = createElement('label', 'user-row member-row');
    row.appendChild(createElement('div', 'user-row-avatar', initials(name)));
    row.appendChild(info);
    row.appendChild(checkbox);
    return row;
  }

  /* =====================================================
     DOM factories: notifications
     ===================================================== */

  function notificationTitle(notification) {
    return notification.type === 'friend'
      ? notification.name + ' ' + notification.text
      : notification.name + ' ' + notification.text + ' #' + notification.group;
  }

  /*
  HTML Skeleton Reference:
  <div class="btn-group">
    <button class="btn btn-primary" type="button" data-action="accept">Accept | Join</button>
    <button class="btn btn-secondary" type="button" data-action="decline">Decline</button>
  </div>
  */
  function createNotificationActions(notification) {
    const accept = createElement(
      'button',
      'btn btn-primary',
      notification.type === 'friend' ? 'Accept' : 'Join'
    );
    accept.type = 'button';
    accept.dataset.action = 'accept';

    const decline = createElement('button', 'btn btn-secondary', 'Decline');
    decline.type = 'button';
    decline.dataset.action = 'decline';

    const actions = createElement('div', 'btn-group');
    actions.append(accept, decline);
    return actions;
  }

  /*
  HTML Skeleton Reference:
  <div class="user-row notif-item" data-notification-id="n1">
    <div class="notif-icon">
      <span class="material-symbols-outlined">person_add | group_add</span>
    </div>
    <div class="user-row-info">
      <span class="user-row-name">Priya Nair sent you a friend request</span>
      <span class="user-row-sub">5m ago</span>
      <div class="btn-group">...</div>
    </div>
  </div>
  */
  function createNotificationItem(notification) {
    const icon = createElement('div', 'notif-icon');
    icon.appendChild(createIcon(notification.type === 'friend' ? 'person_add' : 'group_add'));

    const info = createElement('div', 'user-row-info');
    info.appendChild(createElement('span', 'user-row-name', notificationTitle(notification)));
    info.appendChild(createElement('span', 'user-row-sub', notification.time));
    info.appendChild(createNotificationActions(notification));

    const row = createElement('div', 'user-row notif-item');
    row.dataset.notificationId = notification.id;
    row.appendChild(icon);
    row.appendChild(info);
    return row;
  }

  /* =====================================================
     DOM factories: messages
     ===================================================== */

  /*
  HTML Skeleton Reference:
  <div class="date-divider">
    <div class="date-divider-line-wrap">
      <div class="date-divider-line"></div>
    </div>
    <span class="date-divider-label">Today, October 24, 2024</span>
  </div>
  */
  function createDateDivider(label) {
    const lineWrap = createElement('div', 'date-divider-line-wrap');
    lineWrap.appendChild(createElement('div', 'date-divider-line'));

    const divider = createElement('div', 'date-divider');
    divider.appendChild(lineWrap);
    divider.appendChild(createElement('span', 'date-divider-label', label));
    return divider;
  }

  /*
  HTML Skeleton Reference:
  <div class="message-avatar-wrap">
    <!-- with a photo -->
    <img class="message-avatar" alt="Marcus Vance" src="https://..." />
    <!-- without a photo -->
    <div class="message-avatar-initials">AM</div>
    <span class="status-dot is-online"></span>
  </div>
  */
  function createMessageAvatar(message) {
    const wrap = createElement('div', 'message-avatar-wrap');

    if (message.avatarUrl) {
      const photo = createElement('img', 'message-avatar');
      photo.setAttribute('alt', message.author);
      photo.setAttribute('src', message.avatarUrl);
      wrap.appendChild(photo);
    } else {
      wrap.appendChild(createElement('div', 'message-avatar-initials', initials(message.author)));
    }

    wrap.appendChild(createElement('span', 'status-dot is-' + (message.status || 'online')));
    return wrap;
  }

  /*
  HTML Skeleton Reference:
  <div class="message-header">
    <span class="message-author">Marcus Vance</span>
    <span class="role-badge role-staff">Staff Eng</span>
    <span class="message-time">09:41 AM</span>
  </div>
  */
  function createMessageHeader(message) {
    const header = createElement('div', 'message-header');
    header.appendChild(createElement('span', 'message-author', message.author));
    header.appendChild(createElement('span', 'role-badge role-' + message.role.variant, message.role.label));
    header.appendChild(createElement('span', 'message-time', message.time));
    return header;
  }

  /*
  HTML Skeleton Reference:
  <p class="message-text [has-attachment]">
    Plain text part
    <code class="inline-code">inline code part</code>
    Plain text part
  </p>
  */
  function createMessageText(parts, hasAttachment) {
    const paragraph = createElement('p', 'message-text' + (hasAttachment ? ' has-attachment' : ''));

    parts.forEach(function (part) {
      if (part.type === 'code') {
        paragraph.appendChild(createElement('code', 'inline-code', part.value));
      } else {
        paragraph.appendChild(document.createTextNode(part.value));
      }
    });
    return paragraph;
  }

  /*
  HTML Skeleton Reference:
  <pre class="code-block-content" id="code-block-m2">
    <span class="token-keyword">export const</span> plain text <span class="token-string">'...'</span> ...
  </pre>
  */
  function createCodeContent(tokens, codeId) {
    const pre = createElement('pre', 'code-block-content');
    pre.id = codeId;

    tokens.forEach(function (token) {
      if (token.type) {
        pre.appendChild(createElement('span', 'token-' + token.type, token.text));
      } else {
        pre.appendChild(document.createTextNode(token.text));
      }
    });
    return pre;
  }

  /*
  HTML Skeleton Reference:
  <div class="code-block">
    <div class="code-block-header">
      <div class="code-block-title">
        <span class="material-symbols-outlined">data_object</span>
        <span>tokenObserver.ts</span>
      </div>
      <button class="code-copy-btn" type="button" data-copy-target="code-block-m2">
        <span class="material-symbols-outlined">content_copy</span>
        <span>Copy Code</span>
      </button>
    </div>
    <pre class="code-block-content" id="code-block-m2">...</pre>
  </div>
  */
  function createCodeBlock(attachment, message) {
    const codeId = 'code-block-' + message.id;

    const title = createElement('div', 'code-block-title');
    title.appendChild(createIcon('data_object'));
    title.appendChild(createElement('span', '', attachment.fileName));

    const copyButton = createElement('button', 'code-copy-btn');
    copyButton.type = 'button';
    copyButton.dataset.copyTarget = codeId;
    copyButton.appendChild(createIcon('content_copy'));
    copyButton.appendChild(createElement('span', '', 'Copy Code'));

    const header = createElement('div', 'code-block-header');
    header.appendChild(title);
    header.appendChild(copyButton);

    const block = createElement('div', 'code-block');
    block.appendChild(header);
    block.appendChild(createCodeContent(attachment.tokens, codeId));
    return block;
  }

  /*
  HTML Skeleton Reference:
  <div class="file-card">
    <div class="file-card-info">
      <div class="file-card-icon">
        <span class="material-symbols-outlined">picture_as_pdf</span>
      </div>
      <div class="file-card-details">
        <div class="file-card-name-row">
          <span class="file-card-name">Q3_Design_Review_v2.pdf</span>
          <span class="material-symbols-outlined file-card-verified" title="Verified Architecture Document">verified</span>
        </div>
        <span class="file-card-meta">4.2 MB • PDF Document</span>
      </div>
    </div>
    <button class="file-card-download-btn" type="button" title="Download Document">
      <span class="material-symbols-outlined">download</span>
    </button>
  </div>
  */
  function createFileCard(attachment) {
    const icon = createElement('div', 'file-card-icon');
    icon.appendChild(createIcon(attachment.icon));

    const verified = createIcon('verified', 'file-card-verified');
    verified.setAttribute('title', attachment.verifiedTitle);

    const nameRow = createElement('div', 'file-card-name-row');
    nameRow.appendChild(createElement('span', 'file-card-name', attachment.name));
    nameRow.appendChild(verified);

    const details = createElement('div', 'file-card-details');
    details.appendChild(nameRow);
    details.appendChild(createElement('span', 'file-card-meta', attachment.meta));

    const info = createElement('div', 'file-card-info');
    info.appendChild(icon);
    info.appendChild(details);

    const download = createElement('button', 'file-card-download-btn');
    download.type = 'button';
    download.setAttribute('title', 'Download Document');
    download.appendChild(createIcon('download'));

    const card = createElement('div', 'file-card');
    card.appendChild(info);
    card.appendChild(download);
    return card;
  }

  /*
  HTML Skeleton Reference:
  <button class="image-card-action-btn" type="button" title="Zoom in">
    <span class="material-symbols-outlined">zoom_in</span>
  </button>
  */
  function createImageActionButton(iconName, title) {
    const button = createElement('button', 'image-card-action-btn');
    button.type = 'button';
    button.setAttribute('title', title);
    button.appendChild(createIcon(iconName));
    return button;
  }

  /*
  HTML Skeleton Reference:
  <div class="image-card">
    <div class="image-card-preview">
      <img class="image-card-img" alt="Interface design wireframe diagram" src="https://..." />
      <div class="image-card-overlay">
        <div class="image-card-info">
          <span class="image-card-filename">thread_spec_v04.png</span>
          <span class="image-card-meta">2560 × 1440 • 840 KB</span>
        </div>
        <div class="image-card-actions">
          <button class="image-card-action-btn" type="button" title="Zoom in">...</button>
          <button class="image-card-action-btn" type="button" title="Download file">...</button>
        </div>
      </div>
    </div>
  </div>
  */
  function createImageCard(attachment) {
    const picture = createElement('img', 'image-card-img');
    picture.setAttribute('alt', attachment.alt);
    picture.setAttribute('src', attachment.src);

    const info = createElement('div', 'image-card-info');
    info.appendChild(createElement('span', 'image-card-filename', attachment.fileName));
    info.appendChild(createElement('span', 'image-card-meta', attachment.meta));

    const actions = createElement('div', 'image-card-actions');
    actions.appendChild(createImageActionButton('zoom_in', 'Zoom in'));
    actions.appendChild(createImageActionButton('download', 'Download file'));

    const overlay = createElement('div', 'image-card-overlay');
    overlay.appendChild(info);
    overlay.appendChild(actions);

    const preview = createElement('div', 'image-card-preview');
    preview.appendChild(picture);
    preview.appendChild(overlay);

    const card = createElement('div', 'image-card');
    card.appendChild(preview);
    return card;
  }

  const attachmentFactories = {
    code: createCodeBlock,
    file: createFileCard,
    image: createImageCard
  };

  /*
  HTML Skeleton Reference:
  <div class="message [message-new]">
    <div class="message-avatar-wrap">...</div>
    <div class="message-body">
      <div class="message-header">...</div>
      <p class="message-text [has-attachment]">...</p>
      <!-- optional: code-block | file-card | image-card -->
    </div>
  </div>
  */
  function createMessage(message) {
    const body = createElement('div', 'message-body');
    body.appendChild(createMessageHeader(message));
    body.appendChild(createMessageText(message.text, Boolean(message.attachment)));
    if (message.attachment) {
      body.appendChild(attachmentFactories[message.attachment.kind](message.attachment, message));
    }

    const element = createElement('div', 'message' + (message.isNew ? ' message-new' : ''));
    element.appendChild(createMessageAvatar(message));
    element.appendChild(body);
    return element;
  }


  /* =====================================================
     User menu (avatar, top right)
     ===================================================== */

  const userMenuItems = [
    { id: 'profile', label: 'Profile', icon: 'person' },
    { id: 'settings', label: 'Settings', icon: 'settings' },
    { id: 'logout', label: 'Log out', icon: 'logout', isDanger: true, hasDividerAbove: true }
  ];

  // What each entry does. Replace these bodies with your own UI logic.
  const userMenuActions = {
    profile: async function () { showToast('Profile selected'); },
    settings: async function () { showToast('Settings selected'); },
    logout: async function () { 
      const res = await fetch(`${BASE_URL}/api/logout`, {
        method: 'POST',
        credentials: 'include'
      });
      if (res.ok) {
        window.location.href = '/login.html';
        window.cookieStore.clear(); // Clear cookies on logout
      } else {
        const data = await res.json();
        showError(data.message || 'Logout failed');
      }
    }
  };

  function createUserMenuItem(item) {
    const button = createElement('button', 'user-menu-item' + (item.isDanger ? ' is-danger' : ''));
    button.type = 'button';
    button.setAttribute('role', 'menuitem');
    button.dataset.menuAction = item.id;
    button.appendChild(createIcon(item.icon));
    button.appendChild(createElement('span', '', item.label));
    return button;
  }

  /*
  HTML Skeleton Reference:
  <div class="user-menu-divider" role="separator"></div>
  */
  function createUserMenuDivider() {
    const divider = createElement('div', 'user-menu-divider');
    divider.setAttribute('role', 'separator');
    return divider;
  }

  /*
  HTML Skeleton Reference:
  <div class="user-menu" id="user-menu" role="menu" hidden>
    <div class="user-menu-header">
      <span class="user-menu-name">Alex Mercer</span>
      <span class="user-menu-role">Lead</span>
    </div>
    <button class="user-menu-item" ...>...</button>
    <div class="user-menu-divider" role="separator"></div>
    <button class="user-menu-item is-danger" ...>...</button>
  </div>
  */
  function createUserMenu() {
    const header = createElement('div', 'user-menu-header');
    header.appendChild(createElement('span', 'user-menu-name', currentUser.name));
    header.appendChild(createElement('span', 'user-menu-role', currentUser.role.label));

    const menu = createElement('div', 'user-menu');
    menu.id = 'user-menu';
    menu.setAttribute('role', 'menu');
    menu.hidden = true;
    menu.appendChild(header);

    userMenuItems.forEach(function (item) {
      if (item.hasDividerAbove) menu.appendChild(createUserMenuDivider());
      menu.appendChild(createUserMenuItem(item));
    });
    return menu;
  }

  const userAvatar = document.querySelector('.user-avatar');
  const userMenu = createUserMenu();
  topbarRight.appendChild(userMenu);

  // Make the avatar a keyboard-reachable trigger without touching the HTML
  userAvatar.dataset.menuToggle = 'user-menu';
  userAvatar.setAttribute('role', 'button');
  userAvatar.setAttribute('tabindex', '0');
  userAvatar.setAttribute('aria-haspopup', 'menu');
  userAvatar.setAttribute('aria-controls', 'user-menu');
  userAvatar.setAttribute('aria-expanded', 'false');

  function setUserMenuOpen(isOpen) {
    userMenu.hidden = !isOpen;
    userAvatar.setAttribute('aria-expanded', String(isOpen));
  }

  // One click listener for the whole menu: avatar toggles it, an item runs its
  // action (data-menu-action), and a click anywhere else closes it.
  document.addEventListener('click', async function (event) {
    const item = event.target.closest('[data-menu-action]');
    if (item) {
      await userMenuActions[item.dataset.menuAction]();
      setUserMenuOpen(false);
      return;
    }
    if (event.target.closest('[data-menu-toggle]')) {
      setUserMenuOpen(userMenu.hidden);
      return;
    }
    if (!event.target.closest('.user-menu')) setUserMenuOpen(false);
  });

  // Esc closes it; Enter / Space on the focused avatar opens it
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      setUserMenuOpen(false);
    } else if ((event.key === 'Enter' || event.key === ' ') && event.target === userAvatar) {
      event.preventDefault();
      setUserMenuOpen(userMenu.hidden);
    }
  });


  /* =====================================================
      Logic solving
     ===================================================== */

  // Get list of conversations from the server when the page loads.
  const conversationListRes = await fetch(`${BASE_URL}/api/conversations`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json'
    },
    credentials: 'include'
  });

  if (!conversationListRes.ok) {
    const errorData = await conversationListRes.json();
    showError(errorData.message || 'Failed to load conversations');
  } else {
    const conversationsData = await conversationListRes.json();
    conversations = conversationsData.map(conv => ({
      id: String(conv.conversation_id),
      kind: conv.conversation_type === 'direct' ? 'person' : 'group',
      name: conv.display_name,
      avatarUrl: conv.conversation_img_url || null,
      time: '', // Placeholder, will be updated when messages are loaded
      preview: '', // Placeholder, will be updated when messages are loaded
      unread: 0 // Placeholder, will be updated when messages are loaded
    }));

    //Render conversations in the sidebar
    conversationList.replaceChildren(
      ...conversations.map(createConversationItem)
    );
  }

  // /* =====================================================
  //    Initial render
  //    ===================================================== */

  // const searchSection = createSearchSection();
  // const searchEmpty = createSearchEmpty();

  // conversationList.append(
  //   ...conversations.map(createConversationItem),
  //   searchSection,
  //   searchEmpty
  // );

  // messageStream.append(
  //   createDateDivider(messageThread.dateLabel),
  //   ...messageThread.messages.map(createMessage)
  // );

  // /* =====================================================
  //    Conversations (one click listener on the list)
  //    ===================================================== */

  // function setActiveConversation(conversationId) {
  //   activeConversationId = conversationId;
  //   conversationList.querySelectorAll('.conversation-item').forEach(function (item) {
  //     item.classList.toggle('is-active', item.dataset.conversationId === conversationId);
  //   });
  // }

  // conversationList.addEventListener('click', function (event) {
  //   const item = event.target.closest('.conversation-item');
  //   if (!item) return;
  //   setActiveConversation(item.dataset.conversationId);
  // });

  // function addConversation(conversation) {
  //   const entry = Object.assign({ id: generateId('c'), time: 'Just now', preview: '', unread: 0 }, conversation);
  //   conversations.unshift(entry);
  //   conversationList.prepend(createConversationItem(entry));
  //   renderSidebarSearch();
  // }

  // /* =====================================================
  //    Sidebar search: people and groups I joined,
  //    plus "Add friend" rows for people I'm not friends with
  //    ===================================================== */

  // function renderSidebarSearch() {
  //   const query = searchInput.value.trim().toLowerCase();
  //   searchClear.hidden = !query;

  //   let matches = 0;
  //   conversationList.querySelectorAll('.conversation-item').forEach(function (item) {
  //     const conversation = findConversation(item.dataset.conversationId);
  //     const show = !query || conversation.name.toLowerCase().includes(query);
  //     item.hidden = !show;
  //     if (show) matches += 1;
  //   });

  //   const strangers = query
  //     ? searchUsers(query).filter(function (user) { return !isFriend(user); })
  //     : [];

  //   searchSection.replaceChildren();
  //   if (strangers.length) {
  //     searchSection.appendChild(createSearchSectionTitle('Add friend'));
  //     strangers.forEach(function (user) { searchSection.appendChild(createUserRow(user)); });
  //   }
  //   searchSection.hidden = strangers.length === 0;
  //   searchEmpty.hidden = !query || matches > 0 || strangers.length > 0;
  // }

  // searchInput.addEventListener('input', renderSidebarSearch);

  // searchClear.addEventListener('click', function () {
  //   searchInput.value = '';
  //   renderSidebarSearch();
  //   searchInput.focus();
  // });

  // /* =====================================================
  //    "Add friend" buttons. The sidebar results and the modal results
  //    are two containers of the same kind, so they share one handler:
  //    the button says who it belongs to through data-user-id.
  //    ===================================================== */

  // function handleAddFriendClick(event) {
  //   const button = event.target.closest('[data-user-id]');
  //   if (!button || button.disabled) return;

  //   const user = findUser(button.dataset.userId);
  //   if (!user) return;

  //   requestedUserIds.add(user.id);
  //   renderSidebarSearch();
  //   renderAddFriendResults();
  //   showToast('Friend request sent to ' + user.name);
  // }

  // searchSection.addEventListener('click', handleAddFriendClick);
  // addFriendResults.addEventListener('click', handleAddFriendClick);

  // /* =====================================================
  //    Modal plumbing (one listener opens, one closes, one handles Esc)
  //    ===================================================== */

  // let lastFocused = null;

  // function renderAddFriendResults() {
  //   const query = addFriendInput.value.trim();
  //   addFriendResults.replaceChildren();

  //   if (!query) {
  //     addFriendResults.appendChild(createHint('Type a name or handle to find people.'));
  //     return;
  //   }

  //   const users = searchUsers(query);
  //   if (!users.length) {
  //     addFriendResults.appendChild(createHint('No users found for "' + query + '".'));
  //     return;
  //   }
  //   users.forEach(function (user) { addFriendResults.appendChild(createUserRow(user)); });
  // }

  // function renderMemberList() {
  //   groupMembers.replaceChildren();
  //   const friends = conversations.filter(function (conversation) {
  //     return conversation.kind === 'person';
  //   });

  //   if (!friends.length) {
  //     groupMembers.appendChild(createHint('Add some friends first.'));
  //     return;
  //   }
  //   friends.forEach(function (friend) { groupMembers.appendChild(createMemberRow(friend.name)); });
  // }

  // function renderNotifications() {
  //   notificationList.replaceChildren();

  //   if (!notifications.length) {
  //     notificationList.appendChild(createHint("You're all caught up."));
  //     return;
  //   }
  //   notifications.forEach(function (notification) {
  //     notificationList.appendChild(createNotificationItem(notification));
  //   });
  // }

  // function updateBadge() {
  //   notifBadge.textContent = String(notifications.length);
  //   notifBadge.hidden = notifications.length === 0;
  // }

  // // What each dialog shows when it opens
  // const modalPreparers = {
  //   'add-friend-modal': function () {
  //     addFriendInput.value = '';
  //     renderAddFriendResults();
  //   },
  //   'create-group-modal': function () {
  //     groupNameInput.value = '';
  //     renderMemberList();
  //     validateGroupForm();
  //   },
  //   'notifications-modal': renderNotifications
  // };

  // function openModal(id) {
  //   const modal = $(id);
  //   if (!modal) return;

  //   if (modalPreparers[id]) modalPreparers[id]();
  //   lastFocused = document.activeElement;
  //   modal.hidden = false;

  //   const firstInput = modal.querySelector('input');
  //   if (firstInput) firstInput.focus();
  // }

  // function closeModal(modal) {
  //   modal.hidden = true;
  //   if (lastFocused && lastFocused.focus) lastFocused.focus();
  // }

  // // Top bar buttons: <button data-modal-target="id-of-modal">
  // topbarRight.addEventListener('click', function (event) {
  //   const trigger = event.target.closest('[data-modal-target]');
  //   if (!trigger) return;
  //   openModal(trigger.dataset.modalTarget);
  // });

  // // Backdrop, X button and Cancel button: anything with data-close
  // document.addEventListener('click', function (event) {
  //   const closeTrigger = event.target.closest('[data-close]');
  //   if (!closeTrigger) return;
  //   closeModal(closeTrigger.closest('.modal'));
  // });

  // document.addEventListener('keydown', function (event) {
  //   if (event.key !== 'Escape') return;
  //   document.querySelectorAll('.modal:not([hidden])').forEach(closeModal);
  // });

  // /* =====================================================
  //    Add friend modal
  //    ===================================================== */

  // addFriendInput.addEventListener('input', renderAddFriendResults);

  // /* =====================================================
  //    Create group modal
  //    ===================================================== */

  // function selectedMembers() {
  //   return Array.from(groupMembers.querySelectorAll('input:checked')).map(function (box) {
  //     return box.value;
  //   });
  // }

  // function validateGroupForm() {
  //   groupSubmit.disabled = !(groupNameInput.value.trim() && selectedMembers().length);
  // }

  // groupNameInput.addEventListener('input', validateGroupForm);

  // // One listener for every checkbox in the member list
  // groupMembers.addEventListener('change', validateGroupForm);

  // groupSubmit.addEventListener('click', function () {
  //   const name = groupNameInput.value.trim().replace(/^#/, '').replace(/\s+/g, '-').toLowerCase();
  //   const members = selectedMembers();
  //   if (!name || !members.length) return;

  //   addConversation({
  //     kind: 'group',
  //     name: name,
  //     preview: 'You created this group with ' + members.length + ' member' + (members.length > 1 ? 's' : '')
  //   });
  //   closeModal($('create-group-modal'));
  //   showToast('Group #' + name + ' created');
  // });

  // /* =====================================================
  //    Notifications (one click listener on the list)
  //    The row carries data-notification-id, so the handler knows
  //    which notification a button belongs to.
  //    ===================================================== */

  // notificationList.addEventListener('click', function (event) {
  //   const actionButton = event.target.closest('[data-action]');
  //   if (!actionButton) return;

  //   const row = actionButton.closest('[data-notification-id]');
  //   const index = notifications.findIndex(function (notification) {
  //     return notification.id === row.dataset.notificationId;
  //   });
  //   if (index === -1) return;

  //   // The notification is dealt with and leaves the list; nothing else happens.
  //   notifications.splice(index, 1);
  //   updateBadge();
  //   renderNotifications();
  // });

  // /* =====================================================
  //    Messages
  //    ===================================================== */

  // function sendMessage() {
  //   const text = chatInput.value.trim();
  //   if (!text) return;

  //   const message = {
  //     id: generateId('m'),
  //     author: currentUser.name,
  //     status: 'online',
  //     role: currentUser.role,
  //     time: 'Just now',
  //     text: [{ type: 'text', value: text }],
  //     attachment: null,
  //     isNew: true
  //   };
  //   messageThread.messages.push(message);

  //   messageStream.appendChild(createMessage(message));
  //   chatInput.value = '';
  //   messageStream.scrollTop = messageStream.scrollHeight;
  // }

  // chatInput.addEventListener('keydown', function (event) {
  //   if (event.key === 'Enter' && !event.shiftKey) {
  //     event.preventDefault();
  //     sendMessage();
  //   }
  // });

  // sendBtn.addEventListener('click', sendMessage);

  // // Copy buttons: <button data-copy-target="id-of-code-element">, one listener for the whole stream
  // messageStream.addEventListener('click', function (event) {
  //   const copyButton = event.target.closest('[data-copy-target]');
  //   if (!copyButton) return;

  //   const target = document.getElementById(copyButton.dataset.copyTarget);
  //   if (target && navigator.clipboard) {
  //     navigator.clipboard.writeText(target.innerText);
  //   }
  // });

  // updateBadge();

})();