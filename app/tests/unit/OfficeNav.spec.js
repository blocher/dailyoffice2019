import { afterEach, describe, expect, it, vi } from 'vitest';
import OfficeNav from '@/components/OfficeNav.vue';

describe('OfficeNav day navigation', () => {
  afterEach(() => vi.useRealTimers());

  it('labels adjacent dates as previous and next', async () => {
    const context = {
      calendarDate: new Date(2026, 9, 15),
      selectedOffice: 'morning_prayer',
      currentServiceType: 'office',
    };

    await OfficeNav.created.call(context);

    expect(context.dayLinks.map(({ text }) => text)).toEqual([
      'Previous',
      'Selected day',
      'Next',
    ]);
    expect(context.dayLinks.map(({ to }) => to)).toEqual([
      '/morning_prayer/2026/10/14',
      '/morning_prayer/2026/10/15',
      '/morning_prayer/2026/10/16',
    ]);
  });

  it('builds a link back to the real current day in the active mode', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 3, 18, 30));

    expect(
      OfficeNav.computed.todayLink.call({
        currentServiceType: 'family',
        selectedOffice: 'close_of_day_prayer',
      })
    ).toBe('/family/close_of_day_prayer/2026/10/3');
    expect(
      OfficeNav.computed.isViewingToday.call({
        calendarDate: new Date(2026, 9, 3, 8),
      })
    ).toBe(true);
    expect(
      OfficeNav.computed.isViewingToday.call({
        calendarDate: new Date(2026, 9, 2, 23, 59),
      })
    ).toBe(false);
  });
});
