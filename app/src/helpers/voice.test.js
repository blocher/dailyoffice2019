import { describe, it, expect, beforeEach, vi } from 'vitest';

vi.mock('@capacitor/app', () => ({
  App: {
    addListener: vi.fn(async () => ({ remove: vi.fn() })),
    getLaunchUrl: vi.fn(async () => undefined),
  },
}));

import {
  AUTOPLAY_WINDOW_MS,
  clearAutoplayRequest,
  pathFromLaunchUrl,
  requestAutoplay,
  takeAutoplayQuery,
  takeAutoplayRequest,
} from './voice';

describe('pathFromLaunchUrl', () => {
  it('reads the app scheme with the open host', () => {
    expect(
      pathFromLaunchUrl('dailyoffice2019://open/office/compline?autoplay=1')
    ).toBe('/office/compline?autoplay=1');
  });

  it('reads the app scheme without the open host', () => {
    expect(pathFromLaunchUrl('dailyoffice2019://family/morning_prayer')).toBe(
      '/family/morning_prayer'
    );
  });

  it('keeps trailing slashes and hashes', () => {
    expect(pathFromLaunchUrl('dailyoffice2019://open/psalm/23/#v4')).toBe(
      '/psalm/23/#v4'
    );
  });

  it('opens today for a bare launch', () => {
    expect(pathFromLaunchUrl('dailyoffice2019://open')).toBe('/');
    expect(pathFromLaunchUrl('dailyoffice2019://open/?autoplay=1')).toBe(
      '/?autoplay=1'
    );
  });

  it('reads the website', () => {
    expect(
      pathFromLaunchUrl('https://www.dailyoffice2019.com/readings/2026/11/3')
    ).toBe('/readings/2026/11/3');
  });

  it('ignores other addresses', () => {
    expect(pathFromLaunchUrl('https://example.com/office/compline')).toBe(null);
    expect(pathFromLaunchUrl('otherapp://open/office')).toBe(null);
    expect(pathFromLaunchUrl('')).toBe(null);
    expect(pathFromLaunchUrl(undefined)).toBe(null);
  });
});

describe('autoplay requests', () => {
  beforeEach(() => clearAutoplayRequest());

  it('takes ?autoplay=1 off the address and remembers the page', () => {
    const redirect = takeAutoplayQuery({
      path: '/office/compline',
      query: { autoplay: '1', other: 'x' },
      hash: '',
    });
    expect(redirect).toEqual({
      path: '/office/compline',
      query: { other: 'x' },
      hash: '',
      replace: true,
    });
    expect(takeAutoplayRequest('/office/compline/')).toBe(true);
    // Once only.
    expect(takeAutoplayRequest('/office/compline')).toBe(false);
  });

  it('leaves addresses without the flag alone', () => {
    expect(takeAutoplayQuery({ path: '/', query: {}, hash: '' })).toBe(null);
  });

  it('does not play when the flag is turned off', () => {
    takeAutoplayQuery({ path: '/', query: { autoplay: '0' }, hash: '' });
    expect(takeAutoplayRequest('/')).toBe(false);
  });

  it('only plays the page it was asked for', () => {
    requestAutoplay('/office/compline', 1000);
    expect(takeAutoplayRequest('/office/morning_prayer', 1000)).toBe(false);
    expect(takeAutoplayRequest('/office/compline', 1000)).toBe(true);
  });

  it('expires', () => {
    requestAutoplay('/', 1000);
    expect(takeAutoplayRequest('/', 1000 + AUTOPLAY_WINDOW_MS + 1)).toBe(false);
    expect(takeAutoplayRequest('/', 1000)).toBe(false);
  });
});
