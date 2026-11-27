/*
  Reading GABC notes for ChantScore.vue
  =====================================
  GABC names staff positions a (the space below the bottom line) to m;
  lines are d, f, h and j. Lowercase is an ordinary note (punctum), upper
  case a diamond (punctum inclinatum). "x" after a position puts a flat
  there (it is not sung); "y" a natural; "." a dot of length. Other marks
  (v, w, _, /, ...) only change a note's look and are ignored here.
*/

const STAFF = 'abcdefghijklm';

// How many times psalter/chant/tones.py tone_demo repeats the reciting note.
export const RECITATION_IN_DEMO = 3;

export function parseGabcNotes(notes) {
  const out = { notes: [], flats: [] };
  const text = notes || '';
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const position = STAFF.indexOf(char.toLowerCase());
    if (position >= 0) {
      const next = text[i + 1];
      if (next === 'x') {
        out.flats.push(position);
        i += 1;
        continue;
      }
      if (next === 'y') {
        i += 1;
        continue;
      }
      out.notes.push({
        position,
        inclinatum: char !== char.toLowerCase(),
        dots: 0,
      });
    } else if (char === '.' && out.notes.length) {
      // ".." after a group of notes dots the last two, one each.
      const doubled = text[i - 1] === '.' && out.notes.length > 1;
      out.notes[out.notes.length - (doubled ? 2 : 1)].dots += 1;
    }
  }
  return out;
}
