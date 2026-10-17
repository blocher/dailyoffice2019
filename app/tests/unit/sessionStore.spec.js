import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// The router loads these with the app; stand-ins keep the test light.
vi.mock('@/views/Pray.vue', () => ({ default: {} }));
vi.mock('@/views/Today.vue', () => ({ default: {} }));
vi.mock('@/views/PageNotFound.vue', () => ({ default: {} }));

const original = Object.getOwnPropertyDescriptor(window, 'sessionStorage');

// What Chrome does with site data blocked: the getter itself throws.
function blockSessionStorage() {
  Object.defineProperty(window, 'sessionStorage', {
    configurable: true,
    get() {
      throw new DOMException(
        "Failed to read the 'sessionStorage' property from 'Window': Access is denied for this document.",
        'SecurityError'
      );
    },
  });
}

async function load() {
  vi.resetModules();
  const { SessionStore } = await import('@/helpers/sessionStore');
  const router = (await import('@/router')).default;
  const Psalms = (await import('@/views/Psalms.vue')).default;
  return { SessionStore, router, Psalms };
}

const from = { name: 'Psalms', fullPath: '/psalms', matched: [{}] };
const to = { name: 'Psalms', fullPath: '/psalms?topic=1', matched: [{}] };

describe('SessionStore with site data blocked', () => {
  beforeEach(blockSessionStorage);

  afterEach(() => {
    Object.defineProperty(window, 'sessionStorage', original);
  });

  it('never throws and keeps values in memory', async () => {
    const { SessionStore } = await load();
    expect(SessionStore.getItem('missing')).toBeNull();
    SessionStore.setItem('flag', 'true');
    expect(SessionStore.getItem('flag')).toBe('true');
    SessionStore.removeItem('flag');
    expect(SessionStore.getItem('flag')).toBeNull();
  });

  it('lets the router decide where to scroll', async () => {
    const { router } = await load();
    expect(router.options.scrollBehavior(to, from, null)).toEqual({ top: 0 });
  });

  it('filters psalms by topic and keeps the scroll position', async () => {
    const { router, Psalms } = await load();
    const view = {
      $router: { replace: vi.fn() },
      updateDisplayedTopic: vi.fn(),
    };

    Psalms.methods.selectTopic.call(view, '1');

    expect(view.$router.replace).toHaveBeenCalledWith({
      name: 'Psalms',
      query: { topic: '1' },
    });
    expect(router.options.scrollBehavior(to, from, null)).toBe(false);
    // The flag is used once; the next navigation scrolls to the top again.
    expect(router.options.scrollBehavior(to, from, null)).toEqual({ top: 0 });
  });
});

describe('SessionStore with working storage', () => {
  beforeEach(() => window.sessionStorage.clear());

  it('persists to sessionStorage', async () => {
    const { SessionStore } = await load();
    SessionStore.setItem('flag', 'true');
    expect(window.sessionStorage.getItem('flag')).toBe('true');
    SessionStore.removeItem('flag');
    expect(window.sessionStorage.getItem('flag')).toBeNull();
  });
});
