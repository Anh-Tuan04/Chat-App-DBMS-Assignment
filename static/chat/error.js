const $ = function (id) { return document.getElementById(id); };

/* =====================================================
   Error notifications (call showError('short message') from any script)
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
const toastElement = document.createElement('div');
    toastElement.className = 'error-toast';
    toastElement.setAttribute('role', 'alert');
    toastElement.dataset.errorId = id;

    const errorIcon = document.createElement('span');
    errorIcon.className = 'material-symbols-outlined';
    errorIcon.textContent = 'error';

    const textElement = document.createElement('p');
    textElement.className = 'error-toast-text';
    textElement.textContent = message;

    const closeButton = document.createElement('button');
    closeButton.className = 'error-toast-close';
    closeButton.type = 'button';
    closeButton.setAttribute('title', 'Dismiss');
    closeButton.dataset.errorClose = '';

    const closeIcon = document.createElement('span');
    closeIcon.className = 'material-symbols-outlined';
    closeIcon.textContent = 'close';

    closeButton.appendChild(closeIcon);
    toastElement.appendChild(errorIcon);
    toastElement.appendChild(textElement);
    toastElement.appendChild(closeButton);

    return toastElement;
}

function dismissError(id) {
    clearTimeout(errorTimers.get(id));
    errorTimers.delete(id);
    const element = errorStack.querySelector('[data-error-id="' + id + '"]');
    if (element) element.remove();
}

/*
HTML Skeleton Reference (card appended to #error-stack):
<div class="error-toast" role="alert" data-error-id="e101">
  ...same as createErrorToast()
</div>
*/
export function showError(message) {
    // generate random id for error
    const id = 'e_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7);
    errorStack.appendChild(createErrorToast(id, message));
    errorTimers.set(id, setTimeout(function () { dismissError(id); }, ERROR_DURATION_MS));
}

// One click listener for every error card: the card says who it is via data-error-id
errorStack.addEventListener('click', function (event) {
    if (!event.target.closest('[data-error-close]')) return;
    dismissError(event.target.closest('[data-error-id]').dataset.errorId);
});
