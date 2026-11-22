import { realTimeSocket } from "../real-time-socket.js";
import { showToast } from "../toast.js"
import { showError } from "../error.js"
/* Avatar menu (top right): Profile, Settings, Log out. Load after chat.js. */
const BASE_URL = 'http://localhost:5000'; // Replace with your actual backend URL

const userAvatar = document.querySelector('.user-avatar');

// const currentUser = {
//   id: localStorage.getItem('userId') || '1', // Default to '1' if not found
//   name: localStorage.getItem('userName') || 'Alex Mercer', // Default to 'Alex Mercer' if not found
//   role: { label: 'Lead', variant: 'lead' }
// };

const currentUser = JSON.parse(
  localStorage.getItem('user') || '{}'
);

const userMenuItems = [
  { id: 'profile', label: 'Profile', icon: 'person' },
  { id: 'settings', label: 'Settings', icon: 'settings' },
  { id: 'logout', label: 'Log out', icon: 'logout', isDanger: true, hasDividerAbove: true }
];

// What each entry does. Replace these bodies with your own UI logic.
const userMenuActions = {
  profile: function () { showToast('Profile selected'); },
  settings: function () { showToast('Settings selected'); },
  logout: async function () { await logout(); }
};


/*
HTML Skeleton Reference:
<tag class="className">text</tag>   <!-- class and text are optional -->
*/
function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text) element.textContent = text;
  return element;
}


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

/*
HTML Skeleton Reference:
<button class="user-menu-item [is-danger]" type="button" role="menuitem" data-menu-action="logout">
  <span class="material-symbols-outlined">logout</span>
  <span>Log out</span>
</button>
*/
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
  header.appendChild(createElement('span', 'user-menu-name', currentUser.username));
  header.appendChild(createElement('span', 'user-menu-role', 'User'));

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

const userMenu = createUserMenu();

/*
HTML Skeleton Reference (added to .topbar-right):
<div class="user-menu" id="user-menu" role="menu" hidden>
  ...same as createUserMenu()
</div>
*/
document.querySelector('.topbar-right').appendChild(userMenu);

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


// handlers for user profile
async function logout() {
  // fetch logout, clear session
  try {
    const res = await fetch(`/api/auth/logout`, {
      method: 'POST',
      credentials: 'include', // Include cookies for session management
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });

    if (res.ok) {
      // Clear local storage
      localStorage.clear();
      realTimeSocket.disconnect(); // Disconnect the socket before redirecting
      // Redirect to login page
      window.location.replace('/');
    } else {
      const errorData = await res.json();
      const errorMessage = errorData?.message || 'Logout failed';
      showError(errorMessage);
    }

  } catch (error) {
    showError('Logout failed: ' + error.message);

  }
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
