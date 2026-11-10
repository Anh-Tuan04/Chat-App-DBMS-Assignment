import { conversationList, createConversationItem } from './conversation.js';


// import { addFriendResults, createUserRow } from "./add-friend.js"
import { renderFriends } from "./friends.js"

import * as UserProfile from "./user-profile.js"


const $ = function (id) { return document.getElementById(id); };


/* =====================================================
   Dialog plumbing (one listener opens, one closes, one handles Esc)
   ===================================================== */

// What each dialog shows when it opens. Each feature script adds its own entry:
// modalPreparers['id-of-modal'] = function () { ... };
const modalPreparers = {
  "friends-modal": renderFriends
};

let lastFocused = null;

function openModal(id) {
  const modal = $(id);
  if (!modal) return;

  if (modalPreparers[id]) modalPreparers[id]();
  lastFocused = document.activeElement;
  modal.hidden = false;

  const firstInput = modal.querySelector('input');
  // Move the typing pointer to the firstInput element and all key events will be captured by it
  if (firstInput) firstInput.focus();
}

function closeModal(modal) {
  modal.hidden = true;
  if (lastFocused && lastFocused.focus) lastFocused.focus();
}

// Top bar buttons: <button data-modal-target="id-of-modal">
document.querySelector(".topbar-right").addEventListener('click', function (event) {
  const trigger = event.target.closest('[data-modal-target]');
  if (!trigger) return;
  openModal(trigger.dataset.modalTarget);
});

// Backdrop, X button and Cancel button: anything with data-close
document.addEventListener('click', function (event) {
  const closeTrigger = event.target.closest('[data-close]');
  if (!closeTrigger) return;
  closeModal(closeTrigger.closest('.modal'));
});

document.addEventListener('keydown', function (event) {
  if (event.key !== 'Escape') return;
  document.querySelectorAll('.modal:not([hidden])').forEach(closeModal);
});


/*
    <!-- ===== Error stack ===== -->
    <div class="error-stack" id="error-stack" aria-live="assertive"></div>

    <!-- ===== Sidebar: conversation list ===== -->
    <nav class="sidebar">
      <div class="sidebar-header">
        <!-- ===== Search bar ===== -->
        <div class="sidebar-search">
          <span class="material-symbols-outlined sidebar-search-icon"
            >search</span
          >
          <input
            class="sidebar-search-input"
            id="sidebar-search-input"
            type="text"
            placeholder="Search people and groups"
            autocomplete="off"
            aria-label="Search people and groups"
          />
          <button
            class="sidebar-search-clear"
            id="sidebar-search-clear"
            type="button"
            title="Clear search"
            hidden
          >
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
      </div>

      <div id="conversation-list" class="conversation-list"></div>
    </nav>

    <!-- ===== Page content ===== -->
    <div class="page-content">
      <!-- Top bar -->
      <header class="topbar">
        <div class="topbar-left">
          <span class="server-name" id="conversation-name">Servername</span>
          <div class="topbar-divider"></div>
        </div>

        <div class="topbar-right">
          <div class="search-box">
            <input
              class="search-input"
              type="text"
              placeholder="Message Search"
            />
            <span class="material-symbols-outlined search-icon">search</span>
          </div>

          <div class="topbar-actions">
            <button
              class="topbar-action-btn"
              id="add-friend-btn"
              data-modal-target="add-friend-modal"
              type="button"
              title="Add Friend"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.75"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                <circle cx="9" cy="7" r="4"></circle>
                <line x1="19" x2="19" y1="8" y2="14"></line>
                <line x1="22" x2="16" y1="11" y2="11"></line>
              </svg>
            </button>
            <button
              class="topbar-action-btn"
              id="create-group-btn"
              data-modal-target="create-group-modal"
              type="button"
              title="Create Group"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.75"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M15 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8" cy="7" r="4"></circle>
                <path d="M19 15v-1a2.5 2.5 0 0 0-2-2.45"></path>
                <circle cx="17" cy="7" r="2.5"></circle>
                <line x1="21" x2="21" y1="2" y2="8"></line>
                <line x1="18" x2="24" y1="5" y2="5"></line>
              </svg>
            </button>
          </div>

          <button
            class="topbar-action-btn friends-btn"
            id="friends-btn"
            data-modal-target="friends-modal"
            type="button"
            title="Friends List"
            aria-label="Friends List"
          >
            <span class="material-symbols-outlined">group</span>
          </button>

          <button
            class="topbar-action-btn notif-btn"
            id="notifications-btn"
            data-modal-target="notifications-modal"
            type="button"
            title="Notifications"
            aria-label="Notifications"
          >
            <span class="material-symbols-outlined">notifications</span>
            <span class="notif-badge" id="notif-badge" hidden>0</span>
          </button>

          <div class="user-avatar">
            <span class="material-symbols-outlined">person</span>
          </div>
        </div>
      </header>

      <!-- Chat area -->
      <main class="chat-main">
        <div class="chat-panel">
          <!-- Message stream -->
          <div class="message-stream" id="message-stream"></div>

          <!-- Composer -->
          <div class="composer">
            <div class="composer-box">
              <div class="composer-row">
                <button
                  class="composer-attach-btn"
                  type="button"
                  title="Attach file or code snippet"
                >
                  <span class="material-symbols-outlined">add_circle</span>
                </button>
                <input
                  class="composer-input"
                  id="chat-input"
                  type="text"
                  placeholder="Message #general-product-core (Press Enter to send, Shift+Enter for new line)"
                />
                <button
                  class="composer-send-btn"
                  id="send-btn"
                  type="button"
                  title="Send Message"
                >
                  <span class="material-symbols-outlined">send</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- ===== Modal: Add friend ===== -->
    <div
      class="modal"
      id="add-friend-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-friend-title"
      hidden
    >
      <div class="modal-backdrop" data-close></div>
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title" id="add-friend-title">Add friend</h3>
          <button class="modal-close" type="button" data-close title="Close">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="modal-body">
          <div class="modal-search">
            <span class="material-symbols-outlined">search</span>
            <input
              id="add-friend-input"
              type="text"
              placeholder="Search by name or handle"
              autocomplete="off"
            />
          </div>
          <div class="modal-results" id="add-friend-results"></div>
        </div>
      </div>
    </div>

    <!-- ===== Modal: Create group ===== -->
    <div
      class="modal"
      id="create-group-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-group-title"
      hidden
    >
      <div class="modal-backdrop" data-close></div>
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title" id="create-group-title">Create group</h3>
          <button class="modal-close" type="button" data-close title="Close">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="modal-body">
          <label class="modal-label" for="group-name-input">Group name</label>
          <input
            class="modal-input"
            id="group-name-input"
            type="text"
            placeholder="e.g. design-systems"
            maxlength="40"
            autocomplete="off"
          />

          <span class="modal-label">Add members</span>
          <div class="modal-results member-list" id="group-members"></div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" type="button" data-close>
            Cancel
          </button>
          <button
            class="btn btn-primary"
            type="button"
            id="create-group-submit"
            disabled
          >
            Create group
          </button>
        </div>
      </div>
    </div>

    <!-- ===== Modal: Friends List ===== -->
    <div
      class="modal"
      id="friends-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="friends-title"
      hidden
    >
      <div class="modal-backdrop" data-close></div>
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title" id="friends-title">Friends</h3>
          <button class="modal-close" type="button" data-close title="Close">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="modal-body">
          <div class="modal-search">
            <span class="material-symbols-outlined">search</span>
            <input
              id="friends-search-input"
              type="text"
              placeholder="Search friends..."
              autocomplete="off"
            />
          </div>
          <div class="modal-results" id="friends-list"></div>
        </div>
      </div>
    </div>

    <!-- ===== Modal: Friends List ===== -->
    <div
      class="modal"
      id="friends-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="friends-title"
      hidden
    >
      <div class="modal-backdrop" data-close></div>
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title" id="friends-title">Friends</h3>
          <button class="modal-close" type="button" data-close title="Close">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="modal-body">
          <div class="modal-search">
            <span class="material-symbols-outlined">search</span>
            <input
              id="friends-search-input"
              type="text"
              placeholder="Search friends..."
              autocomplete="off"
            />
          </div>
          <div class="modal-results" id="friends-list"></div>
        </div>
      </div>
    </div>

    <!-- ===== Modal: Notifications ===== -->
    <div
      class="modal"
      id="notifications-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="notifications-title"
      hidden
    >
      <div class="modal-backdrop" data-close></div>
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title" id="notifications-title">Notifications</h3>
          <button class="modal-close" type="button" data-close title="Close">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>
        <div class="modal-body">
          <div class="modal-results" id="notification-list"></div>
        </div>
      </div>
    </div>

    <div class="toast" id="toast" role="status" aria-live="polite" hidden></div>
    <script src="/static/chat/chat.js" type="module"></script>

*/