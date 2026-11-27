import axios from 'axios';
import { DynamicStorage } from '@/helpers/storage';

/*
  The canticle library
  ====================
  One request (api/v1/canticles) holds every canticle, both language styles,
  and the tables of each canticle rotation. It is kept for offline use like
  the psalter, and held in memory here so moving between the list and a
  canticle does not ask for it again.

  The helpers below turn the rotation tables into "appointments" (where and
  when a canticle is said) and filter and search the library with them.
*/

const STYLE_KEY = 'canticleStyle';

let pending = null;

export async function loadCanticleLibrary() {
  if (!pending) {
    pending = axios
      .get(`${import.meta.env.VITE_API_URL}api/v1/canticles`)
      .then((response) => response.data)
      .catch((error) => {
        pending = null;
        throw error;
      });
  }
  return pending;
}

// For tests.
export function resetCanticleLibrary() {
  pending = null;
}

// The language style last chosen on these pages, else the user's setting.
export async function getCanticleStyle(settings) {
  let stored;
  try {
    stored = await DynamicStorage.getItem(STYLE_KEY);
  } catch {
    // Unreadable storage: fall back to the setting.
  }
  if (stored === 'traditional' || stored === 'contemporary') return stored;
  return settings?.language_style === 'traditional'
    ? 'traditional'
    : 'contemporary';
}

export async function setCanticleStyle(style) {
  try {
    await DynamicStorage.setItem(STYLE_KEY, style);
  } catch {
    // Not remembered; the choice still holds for this visit.
  }
}

// Seasons the invitatories are tied to (they have their own setting rather
// than a rotation table).
const INVITATORY_SEASONS = { 'pascha-nostrum': ['easter'] };

/*
  Every place a canticle is appointed, as
  { rotation, office, slot, days, dayLabel, seasons, note }.
  rotation is null for texts said whatever the canticle rotation (the
  invitatories, the evening hymn, Compline); days and seasons are null when
  the appointment holds on every day or in every season.
*/
export function buildAppointments(library) {
  const bySlug = {};
  const add = (slug, appointment) => {
    (bySlug[slug] ||= []).push(appointment);
  };
  const slotOffice = Object.fromEntries(
    library.slots.map((slot) => [slot.key, slot.office])
  );

  for (const rotation of library.rotations) {
    for (const row of rotation.rows) {
      for (const slot of library.slots) {
        for (const group of row.cells[slot.key] || []) {
          for (const slug of group.canticles) {
            add(slug, {
              rotation: rotation.key,
              office: slot.office,
              slot: slot.key,
              days: row.days.length === 8 ? null : row.days,
              dayLabel: row.days.length === 8 ? null : row.label,
              seasons: group.seasons.length ? group.seasons : null,
              note: null,
            });
          }
        }
      }
    }
    for (const note of rotation.notes) {
      for (const slug of note.canticles) {
        add(slug, {
          rotation: rotation.key,
          office: slotOffice[note.slot],
          slot: note.slot,
          days: null,
          seasons: null,
          note: note.text,
        });
      }
    }
  }

  for (const rotation of library.invitatory_rotations) {
    for (const appointment of rotation.appointments) {
      for (const slug of appointment.canticles) {
        const already = (bySlug[slug] || []).some(
          (a) => a.slot === 'invitatory'
        );
        if (already) continue;
        add(slug, {
          rotation: null,
          office: 'morning',
          slot: 'invitatory',
          days: null,
          seasons: INVITATORY_SEASONS[slug] || null,
          note: null,
        });
      }
    }
  }

  for (const canticle of library.canticles) {
    if (canticle.slots.includes('evening_hymn')) {
      add(canticle.slug, {
        rotation: null,
        office: 'evening',
        slot: 'evening_hymn',
        days: null,
        seasons: null,
        note: null,
      });
    }
    if (canticle.slots.includes('compline')) {
      add(canticle.slug, {
        rotation: null,
        office: 'compline',
        slot: 'compline',
        days: null,
        seasons: null,
        note: null,
      });
    }
  }
  return bySlug;
}

// Curly quotes, dashes and case don't matter when searching.
export function normalize(text) {
  return String(text || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[‘’ʼ]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[–—]/g, '-')
    .replace(/[*|]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/*
  Where a search matches a canticle: 'title' when it matches the name or
  citation, else the first line of the text (in the chosen style) that
  contains it. null when it does not match.
*/
export function searchCanticle(canticle, query, style = 'contemporary') {
  const q = normalize(query);
  if (!q) return { where: 'all' };
  const titles = [
    canticle.latin_name,
    canticle.english_name,
    canticle.citation,
  ];
  if (titles.some((title) => normalize(title).includes(q))) {
    return { where: 'title' };
  }
  const styles =
    style === 'traditional'
      ? ['traditional', 'contemporary']
      : ['contemporary', 'traditional'];
  for (const s of styles) {
    const line = (canticle.texts[s] || []).find((l) =>
      normalize(l.content).includes(q)
    );
    if (line) return { where: 'text', line: line.content, style: s };
  }
  return null;
}

export function matchesAppointment(appointment, filters) {
  const { rotation, office, day, season } = filters;
  if (rotation && appointment.rotation && appointment.rotation !== rotation)
    return false;
  if (office && appointment.office !== office) return false;
  if (day && appointment.days && !appointment.days.includes(day)) return false;
  if (season && appointment.seasons && !appointment.seasons.includes(season))
    return false;
  return true;
}

export function hasFilters(filters) {
  return Boolean(
    filters.rotation || filters.office || filters.day || filters.season
  );
}

/*
  The canticles that match the filters and search, each with the reason it
  matched: [{ canticle, match }].
*/
export function filterCanticles(library, appointments, filters, style) {
  const results = [];
  for (const canticle of library.canticles) {
    if (hasFilters(filters)) {
      const own = appointments[canticle.slug] || [];
      if (!own.some((a) => matchesAppointment(a, filters))) continue;
    }
    const match = searchCanticle(canticle, filters.search, style);
    if (!match) continue;
    results.push({ canticle, match });
  }
  return results;
}

// The JavaScript weekday (0 = Sunday) as the library names it.
const DAY_KEYS = [
  'sunday',
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
];

export function dayKey(date = new Date()) {
  return DAY_KEYS[date.getDay()];
}

// Labels for a list of keys, joined as the book would: "Advent and Lent".
export function listLabel(keys, items) {
  const labels = keys.map(
    (key) => (items.find((item) => item.key === key) || { label: key }).label
  );
  if (labels.length <= 1) return labels.join('');
  return `${labels.slice(0, -1).join(', ')} and ${labels[labels.length - 1]}`;
}

/*
  A sentence-sized summary of a canticle's appointments in one rotation:
  ["Morning Prayer, first canticle: Monday – Friday in Advent", ...].
*/
export function describeAppointments(library, appointments, rotationKey) {
  const slots = Object.fromEntries(library.slots.map((s) => [s.key, s]));
  const offices = Object.fromEntries(
    library.offices.map((o) => [o.key, o.label])
  );
  const groups = new Map();
  for (const a of appointments.filter(
    (a) => a.rotation === rotationKey && !a.note
  )) {
    const label = `${offices[a.office]}, ${slots[a.slot].label.toLowerCase()}`;
    if (!groups.has(label)) groups.set(label, []);
    groups.get(label).push(a);
  }

  return [...groups.entries()].map(([label, list]) => {
    // Every row of the table, in every season, is simply every day.
    const days = new Set(list.flatMap((a) => a.days || []));
    if (
      list.every((a) => !a.seasons) &&
      (list.some((a) => !a.days) || days.size === 8)
    ) {
      return { label, when: ['Every day'] };
    }
    const parts = list.map((a) => {
      const when = a.dayLabel || 'Every day';
      return a.seasons
        ? `${when} in ${listLabel(a.seasons, library.seasons)}`
        : when;
    });
    return { label, when: [...new Set(parts)] };
  });
}
