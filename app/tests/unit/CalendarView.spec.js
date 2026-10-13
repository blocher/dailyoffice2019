import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CalendarView from '../../src/views/Calendar.vue';
import UiKit from '../../src/ui';

const { getItemMock, setItemMock, openWizardMock, openQuickLinksMock } =
  vi.hoisted(() => ({
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

const OCTOBER_2026 = [
  {
    date: '2026-10-01',
    season: { name: 'Season After Pentecost', colors: ['green'] },
    fast: { fast_day: 0 },
    primary_feast: 'Thursday after the Eighteenth Sunday after Pentecost',
    primary_color: 'green',
    major_feast: null,
    major_or_minor_feast: 'Remigius, Bishop of Reims',
    commemorations: [
      { name: 'Thursday', rank: { name: 'FERIA' }, colors: ['green'] },
      {
        uuid: 'remigius',
        name: 'Remigius, Bishop of Reims',
        rank: { name: 'COMMEMORATION_ECUMENICAL' },
        colors: ['white'],
      },
    ],
  },
  {
    date: '2026-10-19',
    season: { name: 'Season After Pentecost', colors: ['green'] },
    fast: { fast_day: 0 },
    primary_feast: 'Luke the Evangelist',
    primary_color: 'red',
    major_feast: 'Luke the Evangelist',
    major_or_minor_feast: 'Luke the Evangelist',
    commemorations: [
      {
        uuid: 'luke',
        name: 'Luke the Evangelist',
        rank: { name: 'HOLY_DAY' },
        colors: ['red'],
      },
    ],
  },
];

function mountCalendar(routeOverrides = {}, days = []) {
  return mount(CalendarView, {
    global: {
      plugins: [UiKit],
      mocks: {
        $http: {
          get: vi.fn().mockResolvedValue({ data: days }),
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
        RouterLink: RouterLinkStub,
      },
    },
  });
}

describe('Calendar view', () => {
  afterEach(() => vi.useRealTimers());

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

  it('still opens the quick links when the app clears the query on load', async () => {
    const wrapper = mountCalendar({
      query: { subscribe: '1', panel: 'quick' },
    });
    // Settings initialization strips the query string on a cold load.
    wrapper.vm.$route.query = {};

    await flushPromises();

    expect(openQuickLinksMock).toHaveBeenCalled();
  });

  it('opens the quick links drawer from the shared calendar event', async () => {
    mountCalendar();

    window.dispatchEvent(
      new window.CustomEvent('open-calendar-subscription', {
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
      new window.CustomEvent('open-calendar-subscription', {
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

  it('offers the feed that matches the view', async () => {
    const wrapper = mountCalendar();
    await flushPromises();
    expect(wrapper.vm.calendarWizardDefaultScope).toBe('major_minor');

    await wrapper.vm.setIncludeMinorFeasts(false);
    expect(wrapper.vm.calendarWizardDefaultScope).toBe('major');
    expect(setItemMock).toHaveBeenCalledWith('calendarFeastFilter', 'major');
  });

  it('shows all feasts unless the reader chose major feasts', async () => {
    const wrapper = mountCalendar(
      { params: { year: '2026', month: '10' } },
      OCTOBER_2026
    );
    await flushPromises();

    expect(getItemMock).toHaveBeenCalledWith('calendarFeastFilter');
    expect(wrapper.vm.includeMinorFeasts).toBe(true);
    expect(wrapper.find('[data-day="2026-10-01"]').text()).toContain(
      'Remigius'
    );
    // Opening the page doesn't save anything; only a choice does.
    expect(setItemMock).not.toHaveBeenCalled();
  });

  it('lays out the month with colors, feasts, and the chosen day', async () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date(2027, 2, 1));
    getItemMock.mockImplementation(async (key) =>
      key === 'calendarFeastFilter' ? 'major' : null
    );
    const wrapper = mountCalendar(
      { params: { year: '2026', month: '10' } },
      OCTOBER_2026
    );
    await flushPromises();

    // October 2026 begins on a Thursday: four blank cells, then 31 days.
    const days = wrapper.findAll('button.day');
    expect(days).toHaveLength(31);
    expect(wrapper.findAll('[role="gridcell"]')).toHaveLength(35);
    expect(wrapper.text()).toContain('October 2026');

    const luke = wrapper.find('[data-day="2026-10-19"]');
    expect(luke.classes()).toContain('is-major');
    expect(luke.find('.day__swatch').classes()).toContain('swatch--red');
    expect(luke.text()).toContain('Luke the Evangelist');

    // Lesser commemorations only show with "All feasts".
    const first = wrapper.find('[data-day="2026-10-01"]');
    expect(first.text()).not.toContain('Remigius');
    await wrapper.vm.setIncludeMinorFeasts(true);
    expect(first.text()).toContain('Remigius');
    expect(first.find('.day__swatch').classes()).toContain('swatch--white');
    expect(setItemMock).toHaveBeenCalledWith('calendarFeastFilter', 'all');

    // The first is chosen by default for a month other than this one.
    expect(first.classes()).toContain('is-selected');
    const detail = wrapper.find('.day-detail');
    expect(detail.text()).toContain('Thursday, October 1');
    const links = detail
      .findAllComponents(RouterLinkStub)
      .map((link) => link.props('to'));
    expect(links).toContain('/commemorations/remigius');
    expect(links).toContain('/morning_prayer/2026/10/1');
    expect(links).toContain('/readings/2026/10/1');
    expect(links).toContain('/day/2026/10/1/');
  });

  it('starts on today in the current month', async () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date(2026, 9, 19, 9));
    const wrapper = mountCalendar({}, OCTOBER_2026);
    await flushPromises();

    const luke = wrapper.find('[data-day="2026-10-19"]');
    expect(luke.classes()).toEqual(
      expect.arrayContaining(['is-today', 'is-selected'])
    );
    expect(luke.attributes('aria-current')).toBe('date');
    expect(luke.attributes('tabindex')).toBe('0');
  });

  it('chooses a day on the first tap and opens it on the second', async () => {
    const wrapper = mountCalendar(
      { params: { year: '2026', month: '10' } },
      OCTOBER_2026
    );
    await flushPromises();

    const luke = wrapper.find('[data-day="2026-10-19"]');
    await luke.trigger('click');
    expect(luke.classes()).toContain('is-selected');
    expect(wrapper.vm.$router.push).not.toHaveBeenCalled();
    expect(wrapper.find('.day-detail').text()).toContain('Luke the Evangelist');

    await luke.trigger('click');
    expect(wrapper.vm.$router.push).toHaveBeenCalledWith({
      name: 'day',
      params: { year: '2026', month: '10', day: '19' },
    });
  });

  it('moves between months', async () => {
    const wrapper = mountCalendar({ params: { year: '2026', month: '12' } });
    await flushPromises();

    await wrapper.find('[aria-label="Next month"]').trigger('click');
    expect(wrapper.vm.$router.push).toHaveBeenLastCalledWith({
      path: '/calendar/2027/1/',
    });

    await wrapper.find('[aria-label="Previous month"]').trigger('click');
    expect(wrapper.vm.$router.push).toHaveBeenLastCalledWith({
      path: '/calendar/2026/12/',
    });
  });
});
