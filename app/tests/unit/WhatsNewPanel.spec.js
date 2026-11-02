import { afterEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';

const push = vi.hoisted(() => vi.fn());
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }));
vi.mock('@capacitor/browser', () => ({ Browser: { open: vi.fn() } }));

import { Browser } from '@capacitor/browser';
import WhatsNewPanel from '@/components/WhatsNewPanel.vue';
import { panels } from '@/helpers/panels';
import { newWhatsNew, setWhatsNew, whatsNewState } from '@/helpers/whatsNew';

const entries = [
  {
    uuid: 'a',
    title: 'Offline mode',
    text: 'Pray anywhere.',
    link: '/offline',
    link_text: 'Set it up',
  },
  {
    uuid: 'b',
    title: 'Book view',
    text: 'Turn the pages.',
    link: 'https://example.com',
    link_text: '',
  },
];

const mounted = [];

function mountPanel() {
  const wrapper = mount(WhatsNewPanel, {
    global: {
      stubs: {
        UiSheet: {
          props: ['subtitle'],
          template: '<div><p class="subtitle">{{ subtitle }}</p><slot /></div>',
        },
        UiIcon: true,
        UiButton: {
          template: '<button @click="$emit(\'click\')"><slot /></button>',
        },
        TransitionGroup: { template: '<ul><slot /></ul>' },
      },
    },
  });
  mounted.push(wrapper);
  return wrapper;
}

async function open() {
  setWhatsNew(entries);
  const wrapper = mountPanel();
  panels.whatsNew = true;
  await wrapper.vm.$nextTick();
  return wrapper;
}

const button = (wrapper, text) =>
  wrapper.findAll('button').find((b) => b.text().startsWith(text));

afterEach(() => {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount());
  window.localStorage.clear();
  whatsNewState.dismissed = [];
  panels.whatsNew = false;
  vi.clearAllMocks();
});

describe('WhatsNewPanel', () => {
  it('says it is loading, or that it failed, rather than "nothing new"', async () => {
    whatsNewState.status = 'loading';
    whatsNewState.entries = [];
    const wrapper = mountPanel();
    panels.whatsNew = true;
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain('Loading');
    setWhatsNew([], { failed: true });
    await wrapper.vm.$nextTick();
    expect(wrapper.text()).toContain('couldn’t load');
    expect(wrapper.text()).not.toContain('Nothing new');
  });

  it('moves focus to the next entry after Got it, and announces it', async () => {
    const wrapper = await open();
    document.body.appendChild(wrapper.element);
    await wrapper.find('[data-got-it]').trigger('click');
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    expect(document.activeElement.textContent).toContain('Book view');
    expect(wrapper.find('[aria-live]').text()).toBe('Offline mode dismissed.');
  });

  it('dismisses nothing when opened', async () => {
    const wrapper = await open();
    expect(newWhatsNew.value).toHaveLength(2);
    expect(wrapper.find('.subtitle').text()).toBe('2 new features');
    expect(wrapper.findAll('.whats-new-entry__new')).toHaveLength(2);
  });

  it('dismisses one entry with Got it, moving it under Earlier', async () => {
    const wrapper = await open();
    await wrapper.find('[data-got-it]').trigger('click');
    expect(newWhatsNew.value.map((e) => e.uuid)).toEqual(['b']);
    expect(wrapper.find('.whats-new__earlier').text()).toContain(
      'Offline mode'
    );
    expect(wrapper.find('.subtitle').text()).toBe('1 new feature');
  });

  it('dismisses one entry with its ×, moving focus to the next ×', async () => {
    const wrapper = await open();
    document.body.appendChild(wrapper.element);
    await wrapper.find('[data-dismiss]').trigger('click');
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();
    expect(newWhatsNew.value.map((e) => e.uuid)).toEqual(['b']);
    expect(document.activeElement.getAttribute('aria-label')).toBe(
      'Dismiss: Book view'
    );
  });

  it('dismisses them all at once', async () => {
    const wrapper = await open();
    await button(wrapper, 'Dismiss all').trigger('click');
    expect(newWhatsNew.value).toEqual([]);
    expect(wrapper.find('.whats-new__earlier-title').text()).toBe(
      'You’re all caught up'
    );
  });

  it('follows a link in the app or the browser, and dismisses that entry', async () => {
    const wrapper = await open();
    await button(wrapper, 'Set it up').trigger('click');
    expect(push).toHaveBeenCalledWith('/offline');
    expect(panels.whatsNew).toBe(false);
    expect(newWhatsNew.value.map((e) => e.uuid)).toEqual(['b']);
    await button(wrapper, 'Try it').trigger('click');
    expect(Browser.open).toHaveBeenCalledWith({ url: 'https://example.com' });
  });
});
