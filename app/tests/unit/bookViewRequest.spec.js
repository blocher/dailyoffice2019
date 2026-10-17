import { afterEach, describe, expect, it } from 'vitest';
import { defineComponent, h } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';
import { createMemoryHistory, createRouter, RouterView } from 'vue-router';
import {
  bookViewRequest,
  onBookViewRequest,
  takeBookViewQuery,
} from '@/helpers/panels';

// A page with a book view, like Office or Readings: its text loads after a
// moment, and it records each time it opens the book.
function bookPage(opened) {
  return defineComponent({
    data: () => ({ text: null, bookOpen: false }),
    created() {
      onBookViewRequest(
        this,
        () => this.text,
        () => {
          this.bookOpen = true;
          opened.push(this.$route.path);
        }
      );
    },
    mounted() {
      setTimeout(() => {
        this.text = 'Lord, have mercy.';
      });
    },
    render() {
      return h('p', this.bookOpen ? 'book' : 'page');
    },
  });
}

let wrapper;
afterEach(() => wrapper?.unmount());

async function setup() {
  bookViewRequest.path = null;
  const opened = [];
  const Page = bookPage(opened);
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: Page, meta: { bookView: true } },
      { path: '/litany/', component: Page, meta: { bookView: true } },
      { path: '/settings', component: { render: () => h('p', 'settings') } },
    ],
  });
  router.beforeEach((to) => takeBookViewQuery(to) || undefined);
  const App = { render: () => h(RouterView, { key: router.currentRoute.value.path }) };
  wrapper = mount(App, { global: { plugins: [router] } });
  return { router, wrapper, opened };
}

async function settle() {
  await flushPromises();
  await new Promise((resolve) => setTimeout(resolve));
  await flushPromises();
}

describe('?book=1', () => {
  it('opens the book on a page that is loading', async () => {
    const { router, opened } = await setup();
    await router.push('/litany/?book=1');
    await settle();
    expect(opened).toEqual(['/litany/']);
    expect(router.currentRoute.value.fullPath).toBe('/litany/');
  });

  it('opens the book on the page already showing', async () => {
    const { router, opened } = await setup();
    await router.push('/litany/');
    await settle();
    expect(opened).toEqual([]);

    // An announcement's link to "?book=1" stays on the current page.
    await router.push('?book=1');
    await settle();
    expect(opened).toEqual(['/litany/']);
    expect(wrapper.text()).toBe('book');
    expect(router.currentRoute.value.fullPath).toBe('/litany/');
  });

  it("opens today's office from a page without a book view", async () => {
    const { router, opened } = await setup();
    await router.push('/settings');
    await settle();
    await router.push('?book=1');
    await settle();
    expect(router.currentRoute.value.fullPath).toBe('/');
    expect(opened).toEqual(['/']);
  });

  it('leaves the request for the page it names', async () => {
    const { router, opened } = await setup();
    await router.push('/');
    await settle();
    await router.push('/litany/?book=1');
    await settle();
    expect(opened).toEqual(['/litany/']);
    expect(bookViewRequest.path).toBe(null);
  });

  it('keeps other query parameters', () => {
    const to = {
      path: '/readings/',
      query: { book: '1', alt: 'x' },
      hash: '#psalm',
      matched: [{ meta: { bookView: true } }],
    };
    expect(takeBookViewQuery(to)).toEqual({
      path: '/readings/',
      query: { alt: 'x' },
      hash: '#psalm',
      replace: true,
    });
    expect(takeBookViewQuery({ ...to, query: {} })).toBe(null);
  });
});
