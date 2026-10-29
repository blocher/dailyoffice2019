/*
  Reader layout
  =============
  The book reader paginates text with CSS columns: the text flows into
  columns exactly one page wide, and turning a page shifts the strip of
  columns sideways. These helpers work out the page geometry for a screen
  and map positions in the strip back to page numbers.

  Each column is one page. On wide, landscape screens two pages show side by
  side as a spread, like an open book.
*/

const PHONE_MAX = 639;

/**
 * Page geometry for a stage of the given size.
 * @param {object} options
 * @param {number} options.width   stage width in px
 * @param {number} options.height  stage height in px
 * @param {number} options.fontSize reading font size in px
 * @param {number} [options.viewportHeight] the window's height in px. The
 *   reader fills the window, so a taller stage means the browser sized it to
 *   its content (one 31,000px "page" on iOS in-app browsers); it is capped.
 * @param {'auto'|'single'|'spread'} [options.spread]
 */
export function computeReaderLayout({
  width,
  height: stageHeight,
  fontSize,
  spread = 'auto',
  viewportHeight,
}) {
  const height =
    viewportHeight > 0 ? Math.min(stageHeight, viewportHeight) : stageHeight;
  const isPhone = width <= PHONE_MAX;
  // Phones show a little desk around the page too, so it reads as a book
  // lying open on a table.
  const outerX = isPhone ? 10 : Math.round(Math.min(48, width * 0.04));
  const outerY = isPhone ? 12 : Math.round(Math.min(40, height * 0.05));
  const padX = isPhone
    ? 20
    : Math.round(Math.max(24, Math.min(64, width * 0.055)));
  const padTop = isPhone ? 46 : 54;
  const padBottom = isPhone ? 46 : 54;

  // A comfortable measure: about 30em of the reading size per page, and no
  // narrower than about 16em when two pages share the screen.
  const maxPageW = Math.round(fontSize * 30);
  const minSpreadPageW = Math.max(300, Math.round(fontSize * 16));

  const availableW = width - outerX * 2;
  const spreadPageW = Math.floor(availableW / 2) - padX * 2;
  const canSpread = !isPhone && spreadPageW >= minSpreadPageW;
  const wantsSpread =
    spread === 'spread' ||
    (spread === 'auto' && width >= 900 && width > height * 1.15);
  const isSpread = canSpread && wantsSpread;
  const cols = isSpread ? 2 : 1;

  const sheetW = Math.floor(Math.min(availableW / cols, maxPageW + padX * 2));
  const sheetH = Math.floor(height - outerY * 2);
  const pageW = Math.max(120, sheetW - padX * 2);
  const pageH = Math.max(120, sheetH - padTop - padBottom);
  const gap = padX * 2;

  return {
    isPhone,
    spread: isSpread,
    cols,
    sheetW,
    sheetH,
    pageW,
    pageH,
    padX,
    padTop,
    padBottom,
    gap,
    // Distance from one column (page) to the next in the strip.
    step: pageW + gap,
    // Width of the visible text window across all pages on screen.
    windowW: pageW * cols + gap * (cols - 1),
  };
}

/** Number of pages (columns) in a strip of the given scroll width. */
export function countPages(scrollWidth, layout) {
  return Math.max(1, Math.round((scrollWidth + layout.gap) / layout.step));
}

/**
 * Page count from two measures of the text strip, so one browser quirk
 * can't hide pages: the strip's scroll width, and where the text ends
 * (`contentEnd`, px from the strip's left edge to the middle of the last
 * character; null when it couldn't be measured). The larger count wins.
 */
export function resolvePageCount({ scrollWidth, contentEnd }, layout) {
  const fromScrollWidth = countPages(scrollWidth, layout);
  const fromContentEnd = Number.isFinite(contentEnd)
    ? pageOfOffset(contentEnd, layout) + 1
    : null;
  return {
    total: Math.max(fromScrollWidth, fromContentEnd || 0),
    fromScrollWidth,
    fromContentEnd,
  };
}

/** Which page (column) an element at this offsetLeft falls on. */
export function pageOfOffset(offsetLeft, layout) {
  return Math.max(0, Math.floor((offsetLeft + 1) / layout.step));
}

/** Number of screens ("views") needed to show every page. */
export function countViews(pages, layout) {
  return Math.max(1, Math.ceil(pages / layout.cols));
}

/** The view that shows a page. */
export function viewOfPage(page, layout) {
  return Math.floor(page / layout.cols);
}

/**
 * The section a page belongs to: the last heading that starts on or before
 * it. `sections` is sorted by page: [{ page, title }].
 */
export function sectionForPage(page, sections) {
  let current = null;
  for (const section of sections) {
    if (section.page <= page) current = section;
    else break;
  }
  return current;
}

/** Pages after this one before the next section starts. */
export function pagesLeftInSection(page, sections, totalPages) {
  const next = sections.find((s) => s.page > page);
  const end = next ? next.page : totalPages;
  return Math.max(0, end - page - 1);
}

/**
 * Whether a drag from this kind of pointer may swipe the book closed. A
 * finger or stylus swipes down to close, as with a sheet; a mouse doesn't,
 * since a slightly heavy click and drag on a desktop shouldn't throw the
 * reader out of the book. Mouse users have Done, the close button, and Escape.
 */
export function canSwipeToClose(pointerType) {
  return pointerType !== 'mouse';
}

/**
 * The block to reopen the book at, given where it was last left. Only the
 * same text (same key, same number of blocks) picks up where it left off;
 * anything else starts from the beginning. Returns a block index or null.
 */
export function resumeBlockIndex(saved, { key, count }) {
  if (!saved || saved.key !== key || saved.count !== count) return null;
  if (!Number.isInteger(saved.index) || saved.index < 0) return null;
  return saved.index < count ? saved.index : null;
}
