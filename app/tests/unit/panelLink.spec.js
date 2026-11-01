import { beforeEach, describe, expect, it } from 'vitest';
import { h } from 'vue';
import { createMemoryHistory, createRouter } from 'vue-router';
import { openPanel, panels, takePanelQuery } from '@/helpers/panels';

function setup() {
  const page = { render: () => h('p') };
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: page },
      { path: '/settings', component: page },
      {
        path: '/offline',
        redirect: { path: '/', query: { panel: 'offline' } },
      },
    ],
  });
  router.beforeEach((to, from) => {
    const redirect = takePanelQuery(to, from);
    return redirect === null ? undefined : redirect;
  });
  return router;
}

describe('a link to a panel', () => {
  beforeEach(() => openPanel(null));

  it('/offline opens the Offline panel over today', async () => {
    const router = setup();
    await router.push('/offline');
    expect(router.currentRoute.value.fullPath).toBe('/');
    expect(panels.offline).toBe(true);
  });

  it('/offline from inside the app stays on the page', async () => {
    const router = setup();
    await router.push('/settings');
    await router.push('/offline');
    expect(router.currentRoute.value.fullPath).toBe('/settings');
    expect(panels.offline).toBe(true);
  });

  it('?panel= works on any page, and leaves the address clean', async () => {
    const router = setup();
    await router.push('/settings?panel=offline&x=1');
    expect(router.currentRoute.value.fullPath).toBe('/settings?x=1');
    expect(panels.offline).toBe(true);
  });

  it('ignores names that are not panels', async () => {
    const router = setup();
    await router.push('/settings?panel=constructor');
    expect(router.currentRoute.value.fullPath).toBe('/settings');
    expect(Object.values(panels).some(Boolean)).toBe(false);
  });
});
