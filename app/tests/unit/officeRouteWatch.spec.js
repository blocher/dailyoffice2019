import { describe, expect, it, vi } from 'vitest';
import Today from '@/views/Today.vue';
import Pray from '@/views/Pray.vue';

vi.mock('@/helpers/storage', () => ({
  DynamicStorage: {
    getItem: vi.fn(() => Promise.resolve(null)),
    setItem: vi.fn(() => Promise.resolve()),
  },
}));

const route = (fullPath, params = {}) => ({ fullPath, params });

describe('office pages and the book view closing', () => {
  it('leaves Today alone when Back lands on the same address', () => {
    const context = { setDate: vi.fn(), currentServiceType: 'office' };

    Today.watch.$route.call(context, route('/'), route('/'));

    expect(context.setDate).not.toHaveBeenCalled();
  });

  it('still updates Today when the address changes', () => {
    const context = { setDate: vi.fn(), currentServiceType: 'office' };

    Today.watch.$route.call(
      context,
      route('/family', { serviceType: 'family' }),
      route('/')
    );

    expect(context.setDate).toHaveBeenCalledOnce();
    expect(context.currentServiceType).toBe('family');
  });

  it('keeps the same date on a dated office page', () => {
    const calendarDate = new Date(2026, 10, 1);
    const context = { calendarDate, office: 'midday_prayer' };
    const here = route('/office/midday_prayer/2026/11/1', {
      serviceType: 'office',
      office: 'midday_prayer',
      year: '2026',
      month: '11',
      day: '1',
    });

    Pray.watch.$route.call(context, here, here);

    expect(context.calendarDate).toBe(calendarDate);
  });
});
