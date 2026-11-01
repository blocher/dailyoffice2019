import { describe, expect, it } from 'vitest';
import { foldFromNative, foldFromSegments } from '@/helpers/fold';

describe('foldFromNative', () => {
  it('reads a fold running top to bottom', () => {
    expect(
      foldFromNative({
        hasFold: true,
        x: 322,
        y: 0,
        width: 25,
        height: 951,
        active: true,
      })
    ).toEqual({ x: 322, width: 25, active: true });
  });

  it('ignores no fold, or one running side to side', () => {
    expect(foldFromNative({ hasFold: false })).toBeNull();
    expect(
      foldFromNative({ hasFold: true, x: 0, y: 322, width: 951, height: 25 })
    ).toBeNull();
    expect(foldFromNative(undefined)).toBeNull();
  });
});

describe('foldFromSegments', () => {
  const left = { left: 0, right: 330, top: 0, bottom: 900 };
  const right = { left: 340, right: 670, top: 0, bottom: 900 };

  it('puts the fold between two side-by-side segments', () => {
    expect(foldFromSegments([right, left], 'folded')).toEqual({
      x: 330,
      width: 10,
      active: true,
    });
    expect(foldFromSegments([left, right], 'continuous').active).toBe(false);
  });

  it('ignores one segment, or two stacked', () => {
    expect(foldFromSegments([left])).toBeNull();
    const top = { left: 0, right: 670, top: 0, bottom: 440 };
    const bottom = { left: 0, right: 670, top: 460, bottom: 900 };
    expect(foldFromSegments([top, bottom])).toBeNull();
  });
});
