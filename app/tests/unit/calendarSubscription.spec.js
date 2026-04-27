import { describe, expect, it } from 'vitest';
import {
  getCalendarDocumentationLinks,
  getCalendarFeedBaseUrl,
  getCalendarFeedUrl,
  getCalendarProviderInstructions,
  getCalendarPrimaryActionLabel,
  getCalendarWizardDefaultScope,
} from '../../src/helpers/calendarSubscription';

describe('calendarSubscription helpers', () => {
  it('builds feed URLs for normal, cancel, and download variants', () => {
    const feedBaseUrl = getCalendarFeedBaseUrl();

    expect(getCalendarFeedUrl('major_minor')).toBe(
      `${feedBaseUrl}/major_minor.ics`
    );
    expect(getCalendarFeedUrl('every', { canceled: true })).toBe(
      `${feedBaseUrl}/every/cancel.ics`
    );
    expect(getCalendarFeedUrl('major', { download: true })).toBe(
      `${feedBaseUrl}/major.ics?download=1`
    );
  });

  it('defaults to the visible calendar scope on the calendar page and to major+commemorations elsewhere', () => {
    expect(
      getCalendarWizardDefaultScope({
        source: 'calendar',
        includeMinorFeasts: false,
      })
    ).toBe('major');
    expect(
      getCalendarWizardDefaultScope({
        source: 'calendar',
        includeMinorFeasts: true,
      })
    ).toBe('major_minor');
    expect(getCalendarWizardDefaultScope({ source: 'menu' })).toBe(
      'major_minor'
    );
  });

  it('lists official documentation for major calendar apps', () => {
    const docs = getCalendarDocumentationLinks();
    expect(docs).toHaveLength(4);
    expect(docs.map((d) => d.value)).toEqual([
      'apple',
      'google',
      'outlook',
      'yahoo',
    ]);
    expect(docs[0].url).toMatch(/^https:\/\//);
  });

  it('provides provider-specific action labels and instruction text', () => {
    expect(getCalendarPrimaryActionLabel('apple', 'subscribe')).toBe(
      'Subscribe in Apple Calendar'
    );
    expect(getCalendarPrimaryActionLabel('google', 'import')).toBe(
      'Download .ics'
    );
    expect(
      getCalendarProviderInstructions('google', 'subscribe').join(' ')
    ).toContain('From URL');
    expect(
      getCalendarProviderInstructions('apple', 'subscribe').join(' ')
    ).toContain('subscribe');
  });
});
