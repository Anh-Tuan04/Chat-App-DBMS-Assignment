import { getConversations } from './conversation.js';
import './real-time-socket.js';
import { prepareAddFriendModal } from "./top-right-bar/add-friend.js"
import { initializeCreateGroup } from "./top-right-bar/create-group.js"
import { prepareFriendsModal } from "./top-right-bar/friends.js"
import { prepareBlockedUsersModal } from "./top-right-bar/blocked-users.js"
import { prepareNotificationsModal } from "./top-right-bar/notifications.js"
import  { replaceAvatarWithInitials } from "./top-right-bar/user-profile.js"

import "./chat-area/messages-actions.js"
import './chat-area/message-delete-actions.js';   // message menu: delete for you / for everyone

import './sidebar-search.js';

const $ = function (id) { return document.getElementById(id); };

/* =====================================================
   Dialog plumbing (one listener opens, one closes, one handles Esc)
   ===================================================== */

// What each dialog shows when it opens. Each feature script adds its own entry:
// modalPreparers['id-of-modal'] = function () { ... };
const modalPreparers = {
  "friends-modal": prepareFriendsModal,
  "add-friend-modal": prepareAddFriendModal,
  "notifications-modal": prepareNotificationsModal,
  "blocked-users-modal": prepareBlockedUsersModal,
  "create-group-modal": initializeCreateGroup
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
document.addEventListener('click', function (event) {
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


getConversations();
replaceAvatarWithInitials();
