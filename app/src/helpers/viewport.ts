// Helpers for stabilizing mobile viewport height, especially iOS Chrome/Safari
// when the browser UI (address/tool bars) expands/collapses.
//
// We expose CSS variables that can be used in layout:
//  - --vvh: visual viewport height in px
//  - --vvh-unit: 1% of visual viewport height in px
//
// Usage in CSS:
//   min-height: var(--vvh);
//   min-height: calc(var(--vvh-unit) * 100);
//
// This complements modern viewport units (dvh/svh) and acts as a pragmatic
// fallback for browsers that misreport vh or fail to trigger resize events.

export function installViewportCssVars(): () => void {
  const docEl = document.documentElement;

  const setVars = () => {
    const vv = window.visualViewport;
    const height = Math.round((vv?.height ?? window.innerHeight) * 100) / 100;
    docEl.style.setProperty('--vvh', `${height}px`);
    docEl.style.setProperty('--vvh-unit', `${height / 100}px`);
  };

  // Initial set
  setVars();

  // iOS Chrome sometimes only fires visualViewport events (not window resize)
  const vv = window.visualViewport;
  vv?.addEventListener('resize', setVars);
  vv?.addEventListener('scroll', setVars);
  window.addEventListener('resize', setVars);
  window.addEventListener('orientationchange', setVars);

  return () => {
    vv?.removeEventListener('resize', setVars);
    vv?.removeEventListener('scroll', setVars);
    window.removeEventListener('resize', setVars);
    window.removeEventListener('orientationchange', setVars);
  };
}
