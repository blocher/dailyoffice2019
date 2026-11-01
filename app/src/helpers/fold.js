/*
  Fold
  ====
  Where a foldable screen divides, so Book view can open a two-page spread
  across the fold like a book (helpers/readerLayout.js).

    - iOS (iPhone Duo): the Fold plugin (ios/App/App/FoldPlugin.swift)
      reports UIKit's division region, active while the phone is half open.
    - Browsers with the Viewport Segments API (Chrome and Android WebView on
      foldables; Safari 27.1 behind a flag): two side-by-side segments mean
      the fold is between them, and Device Posture says whether it's folded.

  foldState.fold is { x, width, active } in CSS px from the window's left
  edge, for a fold running top to bottom, or null.
*/
import { reactive } from 'vue';
import { Capacitor, registerPlugin } from '@capacitor/core';

export const foldState = reactive({ fold: null });

const Fold = registerPlugin('Fold');

export function foldFromNative(data) {
  if (!data?.hasFold || !(data.height > data.width)) return null;
  return { x: data.x, width: data.width, active: Boolean(data.active) };
}

export function foldFromSegments(segments, posture) {
  if (!segments || segments.length !== 2) return null;
  const [left, right] = [...segments].sort((a, b) => a.left - b.left);
  // Side by side, not one above the other.
  if (right.left < left.right - 1) return null;
  return {
    x: left.right,
    width: right.left - left.right,
    active: posture === 'folded',
  };
}

function readSegments() {
  foldState.fold = foldFromSegments(
    window.viewport?.segments,
    navigator.devicePosture?.type
  );
}

export async function watchFold() {
  if (Capacitor.isPluginAvailable('Fold')) {
    try {
      await Fold.addListener('foldChange', (data) => {
        foldState.fold = foldFromNative(data);
      });
      foldState.fold = foldFromNative(await Fold.getFold());
    } catch {
      foldState.fold = null;
    }
    return;
  }
  if (typeof window === 'undefined' || !window.viewport) return;
  readSegments();
  window.addEventListener('resize', readSegments);
  navigator.devicePosture?.addEventListener?.('change', readSegments);
}
