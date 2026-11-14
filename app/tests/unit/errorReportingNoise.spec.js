import { describe, expect, it } from 'vitest';
import { isNoise } from '@/helpers/errorReporting';

const bridge =
  'Object Not Found Matching Id:1, MethodName:update, ParamCount:4';

describe('isNoise', () => {
  it('drops rejections from an injected native bridge', () => {
    const event = {
      errors: [
        {
          errorClass: 'InvalidError',
          errorMessage: 'unhandledrejection handler received a non-error.',
          stacktrace: [],
        },
      ],
      getMetadata: (tab, key) =>
        tab === 'unhandledrejection handler' && key === 'non-error parameter'
          ? bridge
          : undefined,
    };
    expect(isNoise(event)).toBe(true);
  });

  it('keeps other non-error rejections', () => {
    const event = {
      errors: [
        {
          errorClass: 'InvalidError',
          errorMessage: 'unhandledrejection handler received a non-error.',
          stacktrace: [],
        },
      ],
      getMetadata: () => 'something else',
    };
    expect(isNoise(event)).toBe(false);
  });
});
