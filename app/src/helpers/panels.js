/*
  App-level panels
  ================
  Sheets that can be opened from anywhere (header, menu, footer, a page):
    menu      the site menu
    display   theme / text size / font / audio
    share     share your settings
    email     email updates sign-up
    feedback  send feedback
  Each is mounted once in App.vue. Call openPanel('share') to show one.
*/
import { reactive } from 'vue';

export const panels = reactive({
  menu: false,
  display: false,
  share: false,
  email: false,
  feedback: false,
});

export function openPanel(name) {
  Object.keys(panels).forEach((key) => {
    panels[key] = key === name;
  });
}

// ?book=1 asks for a page to open in Book view. The router takes the flag
// off the address and leaves this note, naming the page it is for.
export const bookViewRequest = reactive({ path: null });

export function requestBookView(path) {
  bookViewRequest.path = path;
}

// For a route with ?book=1: notes the request and returns where to go
// instead, without the flag. Pages without a book view (routes lacking
// meta.bookView) open today's office in it.
export function takeBookViewQuery(to) {
  if (!to.query.book) return null;
  if (!to.matched.some((record) => record.meta.bookView)) {
    requestBookView('/');
    return { path: '/', replace: true };
  }
  requestBookView(to.path);
  const query = { ...to.query };
  delete query.book;
  return { path: to.path, query, hash: to.hash, replace: true };
}

// Calls open() once Book view is asked for on this page and ready() is true:
// after the page's text loads, or right away when the request comes while it
// is already showing (an announcement linking to ?book=1). Runs after
// rendering, so a page being navigated away from never takes the request.
export function onBookViewRequest(vm, ready, open) {
  vm.$watch(
    () => bookViewRequest.path === vm.$route.path && Boolean(ready()),
    (go) => {
      if (!go) return;
      bookViewRequest.path = null;
      open();
    },
    { immediate: true, flush: 'post' }
  );
}
