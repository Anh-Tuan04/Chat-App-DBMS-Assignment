// This element is a small log that appears for a short time
const toast = document.getElementById('toast');
let toastTimer = null;

export function showToast(text) {
  toast.textContent = text;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { toast.hidden = true; }, 2500);
}