/*
  Office views prayed offline
  ===========================
  An office opened online is counted by the API when the page asks for it
  (analytics/middleware.py). Opened offline, nothing reaches the API, so the
  view waits here and is reported once the app is back online
  (POST /api/v1/analytics/offline_views).
*/
import axios from 'axios';
import { Capacitor } from '@capacitor/core';
import { getClientId } from '@/helpers/clientId';
import * as db from './db';

const MAX_QUEUED = 500;
const BATCH = 100;
let flushing = null;

export async function queueView(info, query) {
  try {
    const all = await db.getAll('views');
    if (all.length >= MAX_QUEUED) return;
    const settings = { ...query };
    delete settings.extra_collects;
    delete settings.include_audio_links;
    await db.put('views', {
      service_type: info.serviceType,
      office: info.office,
      office_date: info.date,
      translation: query.bible_translation || '',
      settings,
      viewed_at: new Date().toISOString(),
    });
  } catch {
    // Analytics must never get in the way.
  }
}

export function flushViews() {
  if (flushing) return flushing;
  flushing = (async () => {
    try {
      const all = await db.getAll('views');
      if (!all.length) return 0;
      let clientId = null;
      try {
        clientId = await getClientId();
      } catch {
        clientId = null;
      }
      let sent = 0;
      for (let i = 0; i < all.length; i += BATCH) {
        const batch = all.slice(i, i + BATCH);
        await axios.post(
          `${import.meta.env.VITE_API_URL || '/'}api/v1/analytics/offline_views`,
          {
            client_id: clientId,
            platform: Capacitor.getPlatform(),
            views: batch.map(({ id, ...view }) => view), // eslint-disable-line no-unused-vars
          }
        );
        await Promise.all(batch.map((view) => db.remove('views', view.id)));
        sent += batch.length;
      }
      return sent;
    } catch {
      return 0;
    } finally {
      flushing = null;
    }
  })();
  return flushing;
}
