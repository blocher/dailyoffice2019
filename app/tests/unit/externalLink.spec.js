import { afterEach, describe, expect, it, vi } from 'vitest';

const browser = vi.hoisted(() => ({ open: vi.fn() }));
vi.mock('@capacitor/browser', () => ({ Browser: browser }));

import { openExternalLink } from '@/helpers/externalLink';

afterEach(() => {
  vi.restoreAllMocks();
  browser.open.mockReset();
});

describe('openExternalLink', () => {
  it('opens the link in the in-app browser', async () => {
    const open = vi.spyOn(window, 'open').mockReturnValue(null);
    await openExternalLink('https://ko-fi.com/dailyoffice');
    expect(browser.open).toHaveBeenCalledWith({
      url: 'https://ko-fi.com/dailyoffice',
    });
    expect(open).not.toHaveBeenCalled();
  });

  it('falls back to the window opener when the bridge cannot display the URL', async () => {
    browser.open.mockRejectedValue(new Error('Unable to display URL'));
    const open = vi.spyOn(window, 'open').mockReturnValue(null);
    await expect(
      openExternalLink('https://ko-fi.com/dailyoffice')
    ).resolves.toBeUndefined();
    expect(open).toHaveBeenCalledWith(
      'https://ko-fi.com/dailyoffice',
      '_blank',
      'noopener,noreferrer'
    );
  });
});
