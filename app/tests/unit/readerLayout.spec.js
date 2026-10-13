import { describe, expect, it } from 'vitest';
import {
  computeReaderLayout,
  countPages,
  countViews,
  pageOfOffset,
  pagesLeftInSection,
  resolvePageCount,
  sectionForPage,
  viewOfPage,
} from '@/helpers/readerLayout';

describe('reader layout', () => {
  it('uses a single page with a little desk around it on phones', () => {
    const layout = computeReaderLayout({
      width: 375,
      height: 812,
      fontSize: 24,
    });
    expect(layout.isPhone).toBe(true);
    expect(layout.spread).toBe(false);
    expect(layout.cols).toBe(1);
    expect(layout.sheetW).toBe(375 - 20);
    expect(layout.pageW).toBe(layout.sheetW - layout.padX * 2);
    expect(layout.windowW).toBe(layout.pageW);
  });

  it('opens a two-page spread on wide landscape screens', () => {
    const layout = computeReaderLayout({
      width: 1440,
      height: 900,
      fontSize: 24,
    });
    expect(layout.spread).toBe(true);
    expect(layout.cols).toBe(2);
    expect(layout.windowW).toBe(layout.pageW * 2 + layout.gap);
    expect(layout.step).toBe(layout.pageW + layout.gap);
    // Pages never grow past a comfortable measure.
    expect(layout.pageW).toBeLessThanOrEqual(24 * 30);
  });

  it('keeps one page on portrait tablets unless asked for two', () => {
    const auto = computeReaderLayout({
      width: 1024,
      height: 1366,
      fontSize: 24,
    });
    expect(auto.spread).toBe(false);
    const forced = computeReaderLayout({
      width: 1024,
      height: 1366,
      fontSize: 18,
      spread: 'spread',
    });
    expect(forced.spread).toBe(true);
  });

  it('falls back to one page when large text would make spreads too narrow', () => {
    const layout = computeReaderLayout({
      width: 1000,
      height: 700,
      fontSize: 42,
    });
    expect(layout.spread).toBe(false);
  });

  it('maps strip positions to pages and views', () => {
    const layout = computeReaderLayout({
      width: 1440,
      height: 900,
      fontSize: 24,
    });
    const pages = countPages(layout.step * 7 - layout.gap, layout);
    expect(pages).toBe(7);
    expect(countViews(pages, layout)).toBe(4);
    expect(pageOfOffset(0, layout)).toBe(0);
    expect(pageOfOffset(layout.step * 3 + 10, layout)).toBe(3);
    expect(viewOfPage(3, layout)).toBe(1);
  });

  it('counts pages from where the text ends when the scroll width falls short', () => {
    const layout = computeReaderLayout({
      width: 390,
      height: 844,
      fontSize: 24,
    });
    // A browser that reports only the first column's width.
    const midPage = (page) => page * layout.step + layout.pageW / 2;
    expect(
      resolvePageCount(
        { scrollWidth: layout.pageW, contentEnd: midPage(66) },
        layout
      )
    ).toEqual({ total: 67, fromScrollWidth: 1, fromContentEnd: 67 });
  });

  it('agrees with the scroll width when both measures work', () => {
    const layout = computeReaderLayout({
      width: 390,
      height: 844,
      fontSize: 24,
    });
    const scrollWidth = layout.step * 12 - layout.gap;
    const contentEnd = 11 * layout.step + 40;
    expect(resolvePageCount({ scrollWidth, contentEnd }, layout)).toEqual({
      total: 12,
      fromScrollWidth: 12,
      fromContentEnd: 12,
    });
  });

  it('falls back to the scroll width when the text end is unknown', () => {
    const layout = computeReaderLayout({
      width: 1440,
      height: 900,
      fontSize: 24,
    });
    const scrollWidth = layout.step * 5 - layout.gap;
    expect(resolvePageCount({ scrollWidth, contentEnd: null }, layout)).toEqual(
      { total: 5, fromScrollWidth: 5, fromContentEnd: null }
    );
    expect(
      resolvePageCount({ scrollWidth: 0, contentEnd: null }, layout)
    ).toEqual({ total: 1, fromScrollWidth: 1, fromContentEnd: null });
  });

  it('finds the section for a page and the pages left in it', () => {
    const sections = [
      { page: 0, title: 'Opening Sentence' },
      { page: 2, title: 'The Psalms' },
      { page: 6, title: 'The Prayers' },
    ];
    expect(sectionForPage(0, sections).title).toBe('Opening Sentence');
    expect(sectionForPage(4, sections).title).toBe('The Psalms');
    expect(pagesLeftInSection(2, sections, 9)).toBe(3);
    expect(pagesLeftInSection(7, sections, 9)).toBe(1);
  });
});
