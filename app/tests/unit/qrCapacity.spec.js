import { describe, expect, it } from 'vitest';
import { fitsInQrCode } from '@/helpers/qrCapacity';

describe('fitsInQrCode', () => {
  it('accepts ordinary links and the byte limit', () => {
    expect(fitsInQrCode('https://www.dailyoffice2019.com/?settings=abc')).toBe(
      true
    );
    expect(fitsInQrCode('a'.repeat(2953))).toBe(true);
    expect(fitsInQrCode('')).toBe(true);
  });

  it('rejects text over the limit, counting bytes not characters', () => {
    expect(fitsInQrCode('a'.repeat(2954))).toBe(false);
    expect(fitsInQrCode('é'.repeat(1500))).toBe(false);
  });
});
