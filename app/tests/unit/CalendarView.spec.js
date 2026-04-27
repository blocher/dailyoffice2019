import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CalendarView from '../../src/views/Calendar.vue';

const { getItemMock, setItemMock, openWizardMock, openQuickLinksMock } = vi.hoisted(() => ({
  getItemMock: vi.fn(),
  setItemMock: vi.fn().mockResolvedValue(),
  openWizardMock: vi.fn(),
  openQuickLinksMock: vi.fn(),
}));

vi.mock('@/helpers/storage', () => ({
  DynamicStorage: {
    getItem: getItemMock,
    setItem: setItemMock,
  },
}));

const CalendarSubscriptionWizardStub = {
  name: 'CalendarSubscriptionWizard',
  template: '<div />',
  methods: {
    openWizard: openWizardMock,
    openQuickLinks: openQuickLinksMock,
  },
};

const ElSwitchStub = {
  props: ['modelValue'],
  emits: ['update:modelValue', 'change'],
  template: '<div />',
};

const ElCalendarStub = {
  props: ['modelValue'],
  template: '<div><slot name="header" :date="\'Calendar\'"></slot></div>',
};

const ElButtonStub = {
  emits: ['click'],
  template: '<button @click="$emit(\'click\', $event)"><slot /></button>',
};

const ElAlertStub = {
  props: ['title'],
  template: '<div>{{ title }}</div>',
};

function mountCalendar(routeOverrides = {}) {
  return mount(CalendarView, {
    global: {
      mocks: {
        $http: {
          get: vi.fn().mockResolvedValue({ data: [] }),
        },
        $route: {
          params: {},
          query: {},
          ...routeOverrides,
        },
        $router: {
          replace: vi.fn().mockResolvedValue(),
          push: vi.fn().mockResolvedValue(),
        },
      },
      stubs: {
        Loading: true,
        CalendarSubscriptionWizard: CalendarSubscriptionWizardStub,
        'el-switch': ElSwitchStub,
        'el-calendar': ElCalendarStub,
        'el-button-group': true,
        'el-button': ElButtonStub,
        'el-alert': ElAlertStub,
      },
    },
  });
}

describe('Calendar view', () => {
  beforeEach(() => {
    getItemMock.mockReset();
    setItemMock.mockReset();
    openWizardMock.mockReset();
    openQuickLinksMock.mockReset();
    getItemMock.mockResolvedValue('false');
    setItemMock.mockResolvedValue();
    window.sessionStorage.clear();
  });

  it('auto-opens the quick links drawer from the subscribe query parameter', async () => {
    const wrapper = mountCalendar({
      query: { subscribe: '1', panel: 'quick' },
    });

    await flushPromises();

    expect(openQuickLinksMock).toHaveBeenCalled();
    expect(wrapper.vm.$router.replace).toHaveBeenCalled();
  });

  it('opens the quick links drawer from the shared calendar event', async () => {
    mountCalendar();

    window.dispatchEvent(
      new CustomEvent('open-calendar-subscription', {
        detail: {
          source: 'menu',
          mode: 'quick',
        },
      })
    );

    await flushPromises();

    expect(openQuickLinksMock).toHaveBeenCalled();
  });

  it('still opens the full wizard when asked directly', async () => {
    mountCalendar();

    window.dispatchEvent(
      new CustomEvent('open-calendar-subscription', {
        detail: {
          source: 'menu',
          app: 'google',
          method: 'subscribe',
        },
      })
    );

    await flushPromises();

    expect(openWizardMock).toHaveBeenCalledWith({
      app: 'google',
      method: 'subscribe',
      scope: 'major_minor',
    });
  });
});
