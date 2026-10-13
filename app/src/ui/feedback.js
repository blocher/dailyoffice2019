/*
  Toasts and confirmations
  ========================
  Imperative helpers so any module (including the Vuex store) can tell the
  reader something or ask a yes/no question. UiFeedbackHost, mounted once in
  App.vue, renders them.

    toast.success('Saved')
    toast.warning({ title: 'Heads up', message: '…', link: { to: '/settings', label: 'Review' } })
    if (await confirm({ title: 'Hide audio?', message: '…', confirmText: 'Hide' })) { … }
*/
import { reactive } from 'vue';

export const feedbackState = reactive({
  toasts: [],
  confirmation: null,
});

let toastId = 0;

function normalize(input, tone) {
  const options = typeof input === 'string' ? { message: input } : input || {};
  return {
    id: ++toastId,
    tone,
    title: options.title || '',
    message: options.message || '',
    link: options.link || null,
    // 0 keeps the toast until it is dismissed
    duration: options.duration ?? (tone === 'error' ? 7000 : 4500),
  };
}

export function dismissToast(id) {
  const index = feedbackState.toasts.findIndex((t) => t.id === id);
  if (index !== -1) feedbackState.toasts.splice(index, 1);
}

function show(input, tone = 'info') {
  const item = normalize(input, tone);
  feedbackState.toasts.push(item);
  if (feedbackState.toasts.length > 3) feedbackState.toasts.shift();
  if (item.duration > 0 && typeof window !== 'undefined') {
    window.setTimeout(() => dismissToast(item.id), item.duration);
  }
  return item.id;
}

export const toast = Object.assign((input) => show(input, 'info'), {
  info: (input) => show(input, 'info'),
  success: (input) => show(input, 'success'),
  warning: (input) => show(input, 'warning'),
  error: (input) => show(input, 'error'),
});

export function confirm(options = {}) {
  return new Promise((resolve) => {
    if (feedbackState.confirmation) {
      feedbackState.confirmation.resolve(false);
    }
    feedbackState.confirmation = {
      title: options.title || 'Are you sure?',
      message: options.message || '',
      confirmText: options.confirmText || 'OK',
      cancelText: options.cancelText || 'Cancel',
      tone: options.tone || 'primary',
      resolve: (value) => {
        feedbackState.confirmation = null;
        resolve(value);
      },
    };
  });
}
