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

export function closePanel(name) {
  panels[name] = false;
}
