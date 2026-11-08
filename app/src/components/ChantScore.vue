<template>
  <figure class="chant-score">
    <svg
      :viewBox="`0 0 ${layout.width} ${HEIGHT}`"
      :style="{ maxWidth: `${layout.width * 1.7}px` }"
      role="img"
      :aria-label="`${label} in chant notation`"
    >
      <g class="chant-score__staff">
        <line
          v-for="line in STAFF_LINES"
          :key="line"
          :x1="2"
          :x2="layout.width - 2"
          :y1="y(line)"
          :y2="y(line)"
        />
      </g>
      <g class="chant-score__clef">
        <path :d="layout.clef" />
      </g>
      <g
        v-for="(group, index) in layout.groups"
        :key="index"
        class="chant-score__group"
        :class="[
          `chant-score__group--${group.role}`,
          { 'is-sung': isActive(group) },
        ]"
      >
        <line
          v-for="(ledger, i) in group.ledgers"
          :key="`l${i}`"
          class="chant-score__ledger"
          :x1="ledger.x - 3"
          :x2="ledger.x + 12"
          :y1="ledger.y"
          :y2="ledger.y"
        />
        <path
          v-for="(flat, i) in group.flats"
          :key="`f${i}`"
          class="chant-score__flat"
          :d="`M${flat.x + 1} ${flat.y - 9} v13 c5 -2 6 -7 0 -6`"
        />
        <path
          v-if="group.accent"
          class="chant-score__accent"
          :d="`M${group.accent.x} ${group.accent.y} l6 -5`"
        />
        <template v-for="(note, i) in group.notes" :key="i">
          <rect
            v-if="note.shape === 'breve'"
            :x="note.x"
            :y="note.y - 4.5"
            width="17"
            height="9"
            class="chant-score__breve"
          />
          <rect
            v-else-if="note.shape === 'square'"
            :x="note.x"
            :y="note.y - 4.5"
            width="9"
            height="9"
          />
          <path
            v-else
            :d="`M${note.x + 4.5} ${note.y - 4.5} l4.5 4.5 l-4.5 4.5 l-4.5 -4.5 z`"
          />
          <circle
            v-for="(dot, d) in note.dots"
            :key="`d${d}`"
            :cx="dot.x"
            :cy="dot.y"
            r="1.7"
          />
        </template>
      </g>
      <g class="chant-score__bars">
        <line :x1="layout.middle" :x2="layout.middle" :y1="y(9)" :y2="y(3)" />
        <text class="chant-score__star" :x="layout.middle - 3.5" :y="y(9) - 6">
          *
        </text>
        <line
          :x1="layout.width - 8"
          :x2="layout.width - 8"
          :y1="y(9)"
          :y2="y(3)"
        />
        <line
          class="chant-score__final"
          :x1="layout.width - 4"
          :x2="layout.width - 4"
          :y1="y(9)"
          :y2="y(3)"
        />
      </g>
    </svg>
    <figcaption class="chant-score__caption">
      {{ label }}
      <span class="chant-score__key"
        >· open note: reciting · hollow: only when needed</span
      >
    </figcaption>
  </figure>
</template>

<script setup>
/*
  A psalm tone in square notation, drawn as SVG from the tone's GABC notes
  (psalter/chant/tones.py tone_score): the clef, the intonation, the
  reciting note as an open breve, the mediation, a bar at the asterisk, the
  reciting note again and the ending. Accent ticks mark notes that need an
  accented syllable; hollow notes are sung only when there are syllables for
  them. Notes of a group are set side by side rather than stacked, which is
  enough to sing from. The group being played by "Hear the tone" is lit.
*/
import { computed } from 'vue';
import { parseGabcNotes, RECITATION_IN_DEMO } from '@/helpers/chantScore';

const props = defineProps({
  // { clef, first_half: [{ n, role }], second_half: [...] }
  score: { type: Object, required: true },
  label: { type: String, default: 'The tone' },
  // { half, index } of the demo note group being played, or null.
  active: { type: Object, default: null },
});

const TOP = 26; // room above the staff for accents and high notes
const HEIGHT = TOP + 44;
const STAFF_LINES = [3, 5, 7, 9]; // d f h j
const GAP = 7;

function y(position) {
  return TOP + (9 - position) * 5;
}

function clefPath(clef) {
  const line = { 1: 3, 2: 5, 3: 7, 4: 9 }[Number(clef.slice(-1))] || 9;
  const cy = y(line);
  // Two small squares straddling the line, joined on the left.
  let d = `M6 ${cy - 7} h7 v5 h-5 v4 h5 v5 h-7 z`;
  if (clef[0] === 'f') {
    // The F clef adds a note with a tail in front of the line.
    d += ` M16 ${cy - 3} h6 v6 h-6 z M16 ${cy - 3} v12 h1.2 v-12 z`;
  }
  return d;
}

const layout = computed(() => {
  let x = props.score.clef?.[0] === 'f' ? 30 : 24;
  const groups = [];
  let middle = 0;
  ['first_half', 'second_half'].forEach((halfKey, half) => {
    (props.score[halfKey] || []).forEach((group, index) => {
      const parsed = parseGabcNotes(group.n);
      const out = {
        role: group.role,
        half,
        index,
        notes: [],
        flats: [],
        ledgers: [],
        accent: null,
      };
      parsed.flats.forEach((position) => {
        out.flats.push({ x, y: y(position) });
        x += 9;
      });
      const startX = x;
      parsed.notes.forEach((note) => {
        const noteY = y(note.position);
        const shape =
          group.role === 'tenor'
            ? 'breve'
            : note.inclinatum
              ? 'diamond'
              : 'square';
        const width = shape === 'breve' ? 17 : 9;
        const onLine = note.position % 2 === 1;
        const dots = [];
        for (let i = 0; i < note.dots; i += 1) {
          dots.push({
            x: x + width + 3 + i * 4.5,
            y: onLine ? noteY - 2.5 : noteY,
          });
        }
        out.notes.push({ x, y: noteY, shape, dots });
        if (note.position >= 11) {
          for (let p = 11; p <= note.position; p += 2) {
            out.ledgers.push({ x, y: y(p) });
          }
        } else if (note.position <= 1) {
          for (let p = 1; p >= note.position; p -= 2) {
            out.ledgers.push({ x, y: y(p) });
          }
        }
        x += width + 1 + (note.dots ? 4 + note.dots * 4.5 : 0);
      });
      if (group.role === 'accent' && parsed.notes.length) {
        const highest = Math.max(...parsed.notes.map((n) => n.position));
        out.accent = { x: startX + 1, y: Math.min(y(highest), y(9)) - 9 };
      }
      groups.push(out);
      x += GAP;
    });
    if (half === 0) {
      x += 2;
      middle = x;
      x += 9;
    }
  });
  return {
    groups,
    middle,
    width: x + 10,
    clef: clefPath(props.score.clef || 'c4'),
  };
});

// The demo repeats the reciting note; map its groups onto the score's.
function scoreIndex(half, demoIndex) {
  const groups = props.score[half === 0 ? 'first_half' : 'second_half'] || [];
  const tenor = groups.findIndex((g) => g.role === 'tenor');
  if (tenor < 0 || demoIndex <= tenor) return demoIndex;
  if (demoIndex < tenor + RECITATION_IN_DEMO) return tenor;
  return demoIndex - (RECITATION_IN_DEMO - 1);
}

function isActive(group) {
  const active = props.active;
  return (
    Boolean(active) &&
    active.half === group.half &&
    scoreIndex(active.half, active.index) === group.index
  );
}
</script>

<style scoped>
.chant-score {
  margin: var(--space-4) auto 0;
  text-align: center;
}

.chant-score svg {
  display: block;
  width: 100%;
  margin: 0 auto;
  color: var(--ink);
  fill: currentColor;
  overflow: visible;
}

.chant-score__staff line,
.chant-score__ledger {
  stroke: var(--accent);
  stroke-width: 0.8;
}

.chant-score__bars line {
  stroke: var(--ink-soft);
  stroke-width: 1;
}

.chant-score__bars .chant-score__final {
  stroke-width: 2.2;
}

.chant-score__flat {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.3;
}

.chant-score__star {
  font-family: var(--font-book);
  font-size: 13px;
  fill: var(--ink-soft);
}

.chant-score__accent {
  stroke: var(--accent);
  stroke-width: 1.6;
  stroke-linecap: round;
  fill: none;
}

.chant-score__breve {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.chant-score__group--return rect,
.chant-score__group--return path {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.4;
}

.chant-score__group.is-sung {
  color: var(--accent);
}

.chant-score__caption {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  color: var(--ink-soft);
}

.chant-score__key {
  color: var(--ink-faint);
}
</style>
