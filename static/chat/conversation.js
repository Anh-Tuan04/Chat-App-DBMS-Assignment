import { showError } from "./error.js"

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
    } else if (initials) {
        const conversationInitials = document.createElement('div');
        conversationInitials.classList.add('conversation-initials');
        conversationInitials.textContent = initials;
        conversationAvatarWrap.appendChild(conversationInitials);
    } else if (isGroup) {
        const conversationChannelAvatar = document.createElement('div');
        conversationChannelAvatar.classList.add('conversation-channel-avatar');
        const tagIcon = document.createElement('span');
        tagIcon.classList.add('material-symbols-outlined');
        tagIcon.textContent = 'tag';
        conversationChannelAvatar.appendChild(tagIcon);
        conversationAvatarWrap.appendChild(conversationChannelAvatar);
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
    preview
}) {
    const conversationItem = document.createElement('div');
    conversationItem.classList.add('conversation-item');
    if (id) {
        conversationItem.setAttribute('data-conversation-id', id);
    }

    const conversationAvatarWrap = createConversationAvatarWrap({avatarUrl, initials, isGroup, status, unreadCount});
    conversationItem.appendChild(conversationAvatarWrap);

    const conversationBody = createConversationBody({name, time, preview});
    conversationItem.appendChild(conversationBody);

    return conversationItem;
}


function renderConversations(conversations) {

}



// handle get conversations from server
async function getConversations() {
    try {
        // const response = await fetch('/api/conversations');
        // const conversations = await response.json();
        // renderConversations(conversations);
    } catch (error) {
        showError('Failed to fetch conversations');
    }
}

conversationList.addEventListener('click', (event) => {
    const conversationItem = event.target.closest('.conversation-item');
    if (!conversationItem) return;
    // Handle conversation item click
});

