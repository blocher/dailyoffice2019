import { beforeEach, describe, expect, it, vi } from 'vitest';
import ShareSettings from '@/components/ShareSettings.vue';

const { clipboardWrite, messageSuccess, messageError } = vi.hoisted(() => ({
  clipboardWrite: vi.fn(),
  messageSuccess: vi.fn(),
  messageError: vi.fn(),
}));

vi.mock('@capacitor/clipboard', () => ({
  Clipboard: { write: clipboardWrite },
}));

vi.mock('@/ui/feedback', () => ({
  toast: Object.assign(vi.fn(), {
    success: messageSuccess,
    error: messageError,
  }),
  confirm: vi.fn(),
}));

const copyLink = () =>
  ShareSettings.methods.copyLink.call({
    getCompactLink: async () => 'https://example.test/?settings=abc',
  });

describe('copying the share link', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('copies the link and says so', async () => {
    clipboardWrite.mockResolvedValueOnce();

    await copyLink();

    expect(clipboardWrite).toHaveBeenCalledWith({
      string: 'https://example.test/?settings=abc',
    });
    expect(messageSuccess).toHaveBeenCalled();
    expect(messageError).not.toHaveBeenCalled();
  });

  it('shows a message when the browser refuses the clipboard write', async () => {
    clipboardWrite.mockRejectedValueOnce(
      Object.assign(new Error('Write permission denied.'), {
        name: 'NotAllowedError',
      })
    );

    await expect(copyLink()).resolves.toBeUndefined();

    expect(messageError).toHaveBeenCalled();
    expect(messageSuccess).not.toHaveBeenCalled();
  });
});
