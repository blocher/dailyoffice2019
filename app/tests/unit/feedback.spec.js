import { afterEach, describe, expect, it } from 'vitest';
import { dismissToast, feedbackState, toast } from '@/ui/feedback';

afterEach(() => {
  [...feedbackState.toasts].forEach((t) => dismissToast(t.id));
});

describe('toasts', () => {
  it('keeps at most three, dropping the oldest', () => {
    ['one', 'two', 'three', 'four'].forEach((message) => toast(message));
    expect(feedbackState.toasts.map((t) => t.message)).toEqual([
      'two',
      'three',
      'four',
    ]);
  });

  it('keeps a toast meant to stay until dismissed', () => {
    toast.info({ message: 'update', duration: 0 });
    ['one', 'two', 'three'].forEach((message) => toast(message));
    expect(feedbackState.toasts.map((t) => t.message)).toEqual([
      'update',
      'two',
      'three',
    ]);
  });
});
