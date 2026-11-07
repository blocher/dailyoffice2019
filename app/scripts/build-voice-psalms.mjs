/*
  Writes the psalm list Siri and Android's assistants search (number, Latin
  title, topics) into both native apps, so "open the De profundis" or "a psalm
  about God's mercy" works offline. The psalter doesn't change; run this again
  only if the API's titles or topics do:

    node scripts/build-voice-psalms.mjs
*/
import { writeFile } from 'node:fs/promises';

const API = process.env.VITE_API_URL || 'https://api.dailyoffice2019.com/';
const TARGETS = [
  new URL('../ios/App/App/Voice/Psalms.json', import.meta.url),
  new URL('../android/app/src/main/res/raw/psalms.json', import.meta.url),
];

const response = await fetch(`${API}api/v1/psalms`);
if (!response.ok) throw new Error(`psalms: HTTP ${response.status}`);
const psalms = (await response.json())
  .map((psalm) => ({
    number: psalm.number,
    latin_title: (psalm.latin_title || '').trim(),
    topics: (psalm.topics || []).map((topic) => topic.topic_name),
  }))
  .sort((a, b) => a.number - b.number);
if (psalms.length !== 150) throw new Error(`expected 150 psalms, got ${psalms.length}`);

const json = `${JSON.stringify(psalms, null, 1)}\n`;
for (const target of TARGETS) {
  await writeFile(target, json);
  console.log(`wrote ${target.pathname}`);
}
