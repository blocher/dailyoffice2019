import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import UiSheet from '@/ui/UiSheet.vue';

function touchEvent(type, target, y, x = 100) {
  const event = new Event(type, { bubbles: true, cancelable: true });
  const touches = type === 'touchend' ? [] : [{ clientX: x, clientY: y }];
  Object.defineProperty(event, 'touches', { value: touches });
  target.dispatchEvent(event);
  return event;
}

function swipe(target, from, to, steps = 5) {
  touchEvent('touchstart', target, from);
  for (let i = 1; i <= steps; i += 1) {
    touchEvent('touchmove', target, from + ((to - from) * i) / steps);
  }
  touchEvent('touchend', target, to);
}

async function mountSheet(props = {}) {
  const wrapper = mount(UiSheet, {
    attachTo: document.body,
    props: { open: true, side: 'float', title: 'Display', ...props },
    slots: {
      default:
        '<div class="content">Body<input type="range" class="slider" /></div>',
    },
    global: { stubs: { UiIcon: true } },
  });
  await nextTick();
  const panel = document.querySelector('.ui-sheet');
  Object.defineProperty(panel, 'offsetHeight', { value: 400 });
  return { wrapper, panel };
}

describe('UiSheet swipe to dismiss', () => {
  beforeEach(() => {
    // Phone width, so the float sheet becomes a bottom sheet.
    window.matchMedia = vi.fn(() => ({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('closes when the grabber is dragged down far enough', async () => {
    const { wrapper } = await mountSheet();
    swipe(document.querySelector('.ui-sheet__grabber'), 100, 300);
    expect(wrapper.emitted('update:open')).toEqual([[false]]);
  });

  it('closes when the header is dragged down', async () => {
    const { wrapper } = await mountSheet();
    swipe(document.querySelector('.ui-sheet__title'), 100, 300);
    expect(wrapper.emitted('update:open')).toEqual([[false]]);
  });

  it('springs back after a short, slow drag', async () => {
    const { wrapper, panel } = await mountSheet();
    const grabber = document.querySelector('.ui-sheet__grabber');
    vi.spyOn(performance, 'now').mockReturnValue(0);
    touchEvent('touchstart', grabber, 100);
    touchEvent('touchmove', grabber, 140);
    await nextTick();
    expect(panel.classList.contains('is-dragging')).toBe(true);
    expect(panel.style.getPropertyValue('--sheet-drag')).toBe('34px');
    vi.spyOn(performance, 'now').mockReturnValue(1000);
    touchEvent('touchmove', grabber, 141);
    touchEvent('touchend', grabber, 141);
    await nextTick();
    expect(wrapper.emitted('update:open')).toBeUndefined();
    expect(panel.classList.contains('is-dragging')).toBe(false);
    expect(panel.style.getPropertyValue('--sheet-drag')).toBe('');
    vi.restoreAllMocks();
  });

  it('drags from the body when it is scrolled to the top', async () => {
    const { wrapper } = await mountSheet();
    swipe(document.querySelector('.content'), 100, 300);
    expect(wrapper.emitted('update:open')).toEqual([[false]]);
  });

  it('lets the body scroll when it is not at the top', async () => {
    const { wrapper } = await mountSheet();
    document.querySelector('.ui-sheet__body').scrollTop = 50;
    const move = (() => {
      const content = document.querySelector('.content');
      touchEvent('touchstart', content, 100);
      const event = touchEvent('touchmove', content, 300);
      touchEvent('touchend', content, 300);
      return event;
    })();
    expect(move.defaultPrevented).toBe(false);
    expect(wrapper.emitted('update:open')).toBeUndefined();
  });

  it('never drags from a slider', async () => {
    const { wrapper } = await mountSheet();
    swipe(document.querySelector('.slider'), 100, 300);
    expect(wrapper.emitted('update:open')).toBeUndefined();
  });

  it('ignores upward swipes', async () => {
    const { wrapper } = await mountSheet();
    swipe(document.querySelector('.ui-sheet__grabber'), 300, 100);
    expect(wrapper.emitted('update:open')).toBeUndefined();
  });

  it('does not drag a desktop float panel', async () => {
    window.matchMedia = vi.fn(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }));
    const { wrapper } = await mountSheet();
    expect(document.querySelector('.ui-sheet__grabber')).toBeNull();
    swipe(document.querySelector('.ui-sheet__title'), 100, 300);
    expect(wrapper.emitted('update:open')).toBeUndefined();
  });
});
