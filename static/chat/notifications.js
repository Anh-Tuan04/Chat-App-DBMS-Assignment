/*
<div class="user-row notif-item" data-notification-id="n1">
  <div class="notif-icon">
    <span class="material-symbols-outlined">person_add</span>   <!-- group_add for group invites -->
  </div>
  <div class="user-row-info">
    <span class="user-row-name">Priya Nair sent you a friend request</span>
    <span class="user-row-sub">5m ago</span>
    <div class="btn-group">
      <button class="btn btn-primary" type="button" data-action="accept">Accept</button>
      <button class="btn btn-secondary" type="button" data-action="decline">Decline</button>
    </div>
  </div>
</div>

*/


const notificationList = document.getElementById('notification-list');

function createNotificationElement({ id, type, message, timeAgo, acceptLabel}) {
    const notifItem = document.createElement('div');
    notifItem.classList.add('user-row', 'notif-item');
    notifItem.dataset.notificationId = id;

    const iconSymbol = document.createElement('span');
    iconSymbol.classList.add('material-symbols-outlined');
    iconSymbol.textContent = type; 

    notifItem.appendChild(iconSymbol);

    const notifInfo = document.createElement('div');
    notifInfo.classList.add('user-row-info');

    const notifName = document.createElement('span');
    notifName.classList.add('user-row-name');
    notifName.textContent = message;

    const notifSub = document.createElement('span');
    notifSub.classList.add('user-row-sub');
    notifSub.textContent = timeAgo;

    const btnGroup = document.createElement('div');
    btnGroup.classList.add('btn-group');

    const acceptBtn = document.createElement('button');
    acceptBtn.classList.add('btn', 'btn-primary');
    acceptBtn.type = 'button';
    acceptBtn.dataset.action = 'accept';
    acceptBtn.textContent = acceptLabel || 'Accept';

    const declineBtn = document.createElement('button');
    declineBtn.classList.add('btn', 'btn-secondary');
    declineBtn.type = 'button';
    declineBtn.dataset.action = 'decline';
    declineBtn.textContent = 'Decline';

    btnGroup.appendChild(acceptBtn);
    btnGroup.appendChild(declineBtn);

    notifInfo.appendChild(notifName);
    notifInfo.appendChild(notifSub);
    notifInfo.appendChild(btnGroup);

    notifItem.appendChild(notifInfo);

    notificationList.appendChild(notifItem);
}

export async function fetchNotifications() {
    try {

    } catch (error) {

    }
}

export async function handleNotificationAction(notificationId, action) {
    try {

    } catch (error) {

    }

}