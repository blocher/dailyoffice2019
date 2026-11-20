import { describe, expect, it, beforeEach } from 'vitest';
import App from '../../src/App.vue';

const { handleScroll, revealHeader } = App.methods;
const { showMenuFab } = App.computed;

describe('App navigation visibility', () => {
  beforeEach(() => {
    window.pageYOffset = 0;
    document.documentElement.scrollTop = 0;
  });

  it('keeps the header visible near the top of the page', () => {
    const state = {
      isHeaderVisible: false,
      headerRevealedByFab: true,
      lastScrollPosition: 120,
    };
    window.pageYOffset = 40;

    handleScroll.call(state);

    expect(state.isHeaderVisible).toBe(true);
    expect(state.headerRevealedByFab).toBe(false);
    expect(state.lastScrollPosition).toBe(40);
    expect(showMenuFab.call(state)).toBe(false);
  });

  it('shows the floating menu control when the header is hidden', () => {
    const state = {
      isHeaderVisible: true,
      headerRevealedByFab: false,
      lastScrollPosition: 0,
    };
    window.pageYOffset = 120;

    handleScroll.call(state);

    expect(state.isHeaderVisible).toBe(false);
    expect(state.lastScrollPosition).toBe(120);
    expect(showMenuFab.call(state)).toBe(true);
  });

  it('reveals the header when the floating menu control is activated', () => {
    const state = {
      isHeaderVisible: false,
      headerRevealedByFab: false,
    };

    revealHeader.call(state);

    expect(state.isHeaderVisible).toBe(true);
    expect(state.headerRevealedByFab).toBe(true);
  });

  it('hides the header again after scrolling down from a revealed menu', () => {
    const state = {
      isHeaderVisible: true,
      headerRevealedByFab: true,
      lastScrollPosition: 120,
    };
    window.pageYOffset = 150;

    handleScroll.call(state);

    expect(state.isHeaderVisible).toBe(false);
    expect(state.headerRevealedByFab).toBe(false);
    expect(state.lastScrollPosition).toBe(150);
    expect(showMenuFab.call(state)).toBe(true);
  });
});
