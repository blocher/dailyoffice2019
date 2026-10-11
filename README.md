# Daily Office, Book of Common Prayer 2019 (https://www.dailyoffice2019.com)

This project is used to build the website https://www.dailyoffice2019.com. It is a Django application written in
Python (to be installed in a development environment). It is used to produce a static html and javascript site which
can then be deployed to the production environment.

## WHAT IS THE SITE FOR?

The site invites you to join with Christians around the world in praying with the Church, at any time or in any place
you may find yourself. It makes it easy to pray daily morning, midday, evening, and compline (bedtime) prayer without
flipping pages, searching for scripture readings or calendars, or interpreting rubrics. The prayers are presented from
The Book of Common Prayer (2019) of the Anglican Church in North America and reflect the ancient patterns of daily
prayer Christians have used since the earliest days of the church.

## WHAT IS THE DAILY OFFICE?

Daily Morning Prayer and Daily Evening Prayer are the established rites (offices) by which, both corporately and
individually, God’s people annually encounter the whole of the Holy Scriptures, daily confess their sins and praise
Almighty God, and offer timely thanksgivings, petitions, and intercessions.

## Contributing

Pull requests are welcome. Take a look at the Github [issues](https://github.com/blocher/dailyoffice2019/issues) and
see where you might help out. Updates to documentation and tests (both of which are largely missing) are also welcome.

### Requirements

- Python 3.12
- Node 16
- PostgreSQL
- Memcached 1.6

The project is known to work with these versions, although it may also work with more recent versions.

### Setting up a development environment

If you are using macOS, all the above requirements may be installed with Homebrew.

#### Initial project setup

- Clone or fork the project from `https://github.com/blocher/dailyoffice2019`
- `cd dailyoffice2019`
- `cp app/.env.development app/.env.local`
- `cp site/website/.env.example site/website/.env`

#### Import database

- Connect to Postgres `psql -d postgres`
- Create database `create database dailyoffice;`
- Create user `create user dailyoffice with password 'password';`
- Grant permissions `grant all privileges on database dailyoffice to dailyoffice;`
- Exit postgres `\q`
- Import `unzip -p site/dailyoffice_2024_01_30.sql.zip dailyoffice_2024_01_30.sql | psql -U dailyoffice dailyoffice`

#### Setup up python environment

- Go to the project's `/site` directory
- Create a Python virtual environment `python3 -m venv env`
- Load virtual environment `source env/bin/activate`
- Install Python Requirements `pip install -r requirements.txt`

#### Run API server (in separate terminal)

- Collect static assets `python manage.py collectstatic`
- Start development server `python manage.py runsslserver`
- The API documentation will be accessible locally at `https://127.0.0.1:8000/api/`

#### Run the client (frontend) server

- Go to the project's `/app` directory
- Follow the setup instructions in the client README: [app/README.md](app/README.md)
- The frontend will be accessible locally at `http://127.0.0.1:8080`

### Patrons and Twilio setup

The `patrons` Django app can send patronal feast and family anniversary reminders by SMS through Twilio. The calendar
feed is protected by an admin-rotatable token; create or rotate that token in Django admin under Patrons -> Calendar
feeds, then subscribe to the generated `.ics` URL in Google Calendar or Outlook.

To configure Twilio:

- Create or log into a Twilio account at https://console.twilio.com/.
- In the Twilio Console, buy or select an SMS-capable United States phone number. Twilio's quickstart documents this
  under Phone Numbers -> Manage -> Buy a number, and the number should be copied in E.164 format such as
  `+15551234567`.
- In the Account Dashboard, copy the Account SID and Auth Token.
- Add these variables to the deployment environment or `site/website/.env`:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_FROM_NUMBER`
  - `PATRONS_SMS_ENABLED=True`
- If sending to United States mobile recipients from a 10-digit long code, complete A2P 10DLC registration in the
  Twilio Console before enabling production reminders.
- Send one test reminder, then confirm the result in Django admin under Patrons -> Text message sends.

Twilio pricing changes over time, but as of the currently published Twilio pricing pages, US SMS starts at `$0.0083`
per sent or received message segment, a leased US long-code number is listed at `$1.15` per month, and sole proprietor
A2P 10DLC registration is listed at about `$4` one-time brand registration, `$15` one-time campaign vetting, and `$2`
per month per campaign. Carrier fees, compliance fees, failed-message fees, and future price changes can apply. Check
the official Twilio pages before budgeting: [Twilio SMS quickstart](https://www.twilio.com/docs/messaging/quickstart),
[Twilio US SMS pricing](https://www.twilio.com/en-us/sms/pricing/us), and
[Twilio A2P 10DLC overview](https://www.twilio.com/en-us/phone-numbers/a2p-10dlc).

### Code formatting standard

- Please use `black` to format code with a line length of 119 beore submitting a pull request
- `find . -iname "*.py" | xargs black --target-version=py311 --line-length=119` from the `site` directory

## Quick overview

The application is built around several Django "apps". The most important are:

- *website*: This is the base site. All settings are defined in `website\settings.py` and all paths are defined
  in `website\routes.py`. Start here.
- *office*: This is where the bulk of the work is down to generate each Office.
- *churchcal*: This is used to build the church calendar. It currently supports both the Anglican Church in North
  America and the Episcopal Church calendars (though only ACNA is currently used for this project)
- *bible*: This is used to retrieve bible passages from various sources (currently only Bible Gateway, but others such
  as the ESV API are coming soon)
- *psalter*: This is used to retrieve passages from the Psalms (currently only the renewed Coverdale translation in the
  Book of Common Prayer 2019)

NOTE: churchcal, bible, and psalter apps may be spun off as separate projects soon and added as dependencies to this
project

## Submitting Issues and Contact

- For feature requests, please submit an issue and label it "enhancement"
- For bug reports, please submit an issue and label it "bug"
- Email the original creator Ben @ feedback@dailyoffice2019.com
- Join the Facebook discussion at: https://www.facebook.com/groups/dailyoffice/

### Initial seven-day Gemini audio batch

`batch_audio_files` is an unscheduled bootstrap command, separate from
`update_audio_files` and on-demand synthesis. It uses Google's asynchronous
[Batch API](https://ai.google.dev/gemini-api/docs/batch-api), with the configured
Gemini 3.8 TTS model, style, and voices. Set `TTS_PROVIDER=gemini` and
`GEMINI_API_KEY` in the command environment. The batch has its own quotas;
it does not guarantee capacity. `ffmpeg` is required for import.

Run from `site/`, using the project's Python environment:

```sh
TTS_PROVIDER=gemini python manage.py batch_audio_files prepare --manifest /absolute/path/initial-audio.json
TTS_PROVIDER=gemini python manage.py batch_audio_files submit --manifest /absolute/path/initial-audio.json
TTS_PROVIDER=gemini python manage.py batch_audio_files status --manifest /absolute/path/initial-audio.json
TTS_PROVIDER=gemini python manage.py batch_audio_files import --manifest /absolute/path/initial-audio.json
```

- `prepare` makes no Google requests. It plans today through six days ahead in
  Django's configured timezone; `--start-date YYYY-MM-DD` and `--days` override
  this. It covers all eight offices, both language styles, the base settings and
  each variation used by the scheduled warmer. It captures the serializer's
  actual grouped prayers, reading paragraphs, and announcements, deduplicates
  them, and skips existing clips. It is not every possible settings combination.
- `submit` creates paid Google batch jobs for the missing clips in chunks of 50
  (set `--batch-size` during preparation to change this, up to 100). Keep the
  manifest: it saves each accepted job so rerunning submission resumes safely.
- `status` checks once; it does not wait or import. Google targets completion
  within 24 hours. Repeat `import` later to import newly completed batches.
- `import` converts successful WAV responses to the same atomic MP3 files and
  `AudioClip` records used by playback. Repeating it preserves existing files.
  Per-clip failures remain listed in the manifest and cause a nonzero exit;
  successful clips are retained. Local conversion or DB failures can be retried
  by importing again. For Google generation failures, finish importing the other
  jobs, then prepare a new manifest for the same date range; cached successes
  will be skipped. Do not prepare duplicate jobs while the originals are pending.

The manifest must be used with the original model/style configuration. A second
process cannot submit/import the same manifest concurrently. An HTTP quota
rejection leaves that chunk ready to submit again later. After an ambiguous
network failure or interruption during submission, the command refuses to submit
that chunk again automatically. Find its matching `dailyoffice-<date>-<manifest
stem>-<chunk>` display name in Google, then recover it with:

```sh
TTS_PROVIDER=gemini python manage.py batch_audio_files attach --manifest /absolute/path/initial-audio.json --chunk 0 --job batches/JOB_ID
```

Import fills the speech-clip cache only. Word alignment, recorded bells, and
assembled full-office tracks continue to use the existing playback pipeline;
the batch does not send synchronous alignment requests. Keep the manifest outside
public media storage. No API key is stored in it.

### Alternate first lessons for Apocrypha

Related request: [#19](https://github.com/blocher/dailyoffice2019/issues/19).
The Readings setting **Apocrypha Readings** defaults to **As appointed**.
**Use alternate readings** opts into the rubric on printed page 737 (PDF page 745)
of the [official BCP 2019 PDF](https://bcp2019.anglicanchurch.net/wp-content/uploads/2019/08/BCP2019.pdf).
When one first lesson is Apocrypha, the other Office's first lesson is divided:
the earlier portion goes to Morning Prayer and the later portion to Evening Prayer,
regardless of which Office originally had the donor. Psalms and second lessons stay
appointed. Sunday/holy-day Eucharistic precedence still runs before substitution.
The Readings overview shows both full and abbreviated alternatives.

**Approved two-year product adaptation:** when the year-selected first lesson is
Apocrypha, use the whole other first lesson (its appointed abbreviation when requested).
Keep the year-selected second lesson. When the selected first lesson is canonical,
keep it. This is a product adaptation; the rubric explicitly describes dividing the
donor between the two Offices. With alternate readings enabled, the Readings overview
also shows the year-selected lessons; its default appointed overview stays unchanged.

The reviewed database contains **57 affected annual records**, not the preliminary
estimate of 55: February 23–24 (Baruch), July 4 (Susanna), October 9–18 (Maccabees),
November 13–December 20 and December 22–24, 29–31 (Judith, Ecclesiasticus/Sirach,
Wisdom). Both `AP` and `DC` tags are included. No separate `HolyDayOfficeDay` row
in the imported snapshot appoints an Apocrypha first lesson. The seed scans their
shared `OfficeDay` parent too and rejects any unreviewed donor pairing. February 24
and October 18 have short NT donors; the July 4 donor is Morning Prayer's Judges 15.
These counts concern stored annual appointments, not the number used in any specific
year after holy-day/Eucharistic precedence.

#### Data migration and deployment prerequisites

Migration `0032` creates a small `AlternateReading` mapping referring to the existing
OfficeDay and Scripture tables. `0033` creates **new Scripture rows for the reviewed
split ranges**, reusing identical existing ranges when present. It does not update the
appointed OfficeDay or whole donor Scripture rows. It runs with historical Django
models and a frozen local extraction helper plus metadata-only JSON. No scripture
text is downloaded or checked into a new licensed-text fixture, and no credentials,
network requests, or synthesis are used by the migration.

A populated deployment must already have exactly one whole Scripture row for each
required full/abbreviated donor, with populated ESV and NRSVCE text. All populated
translation fields must have complete supported verse markup. The extractor preserves
verse chunks, paragraph/poetry containers and retained headings, and rejects unmarked
words, missing verses and chunks crossing a proposed boundary. An incompatible
pre-existing split row is a concrete deployment blocker: the atomic migration fails
with its citation and translation; it never overwrites user text or inserts blanks.
Validate the production copy before deployment. An empty fresh database migrates
successfully without creating blank passages; if lectionary/text data is imported later,
run `python manage.py seed_alternate_readings` to apply the same atomic, idempotent
local seed. The JSON is frozen migration input: future editorial revisions require
a new migration rather than editing deployed migration data.

Two reviewed source exceptions are explicit. RSV 2 Chronicles 20:22 is present but
has a verse-21 HTML class; a checksum-guarded correction of that one chunk's class
allows safe extraction without changing its words or the whole donor. NABRE's Song
of Songs 6–7 donor chapter boundaries use different versification, including a missing
canonical 6:13 and an extra 7:14. The new split rows deliberately leave NABRE unavailable
for those two donors and use the existing NRSVCE fallback. Their canonical citations
must not label different NABRE verses. Chinese/Spanish fields are not populated in
the imported donor snapshot; their existing translation fallback remains available.
Any future populated fields must pass the same markup validation.

Reversing `0033` removes only mappings created by this seed. It **retains Scripture
rows and the appended setting/options**, protecting passages reused elsewhere,
administrator edits and saved user preferences. Reapplication reuses compatible
retained rows. Reversing `0032` removes the mapping table as expected. Existing
setting positions never change: the new share-link character is appended after the
last existing `setting_string_order`. Older short links remain decodable and stored
settings receive the new default through the existing Vuex initialization.

Runtime missing/stale mappings or unusable replacement text fall back to the appointed
first lessons; both split portions must be usable before replacing either. Replacement
citation, testament, rendered text and audio input come from one resolved selection.
The ESV iframe uses the replacement citation only when the replacement actually uses
ESV; other translations/fallbacks omit that iframe. Cached speech receives the selected
text and does not reuse the old Apocrypha passage's content.

#### Reviewed split table

These are editorial proposals for this implementation, reviewed against the actual
stored donor texts and paragraph/narrative transitions; they are not additional printed
BCP appointments. Morning always receives the earlier verses. Unequal lengths are
intentional where they preserve a coherent unit. The rationale flags awkward short
letters, unified poems, speaker changes within a verse and existing abbreviated endings.

| Date | Appointed Apocrypha | Donor Office / whole passage | Morning first lesson | Evening first lesson | Editorial rationale |
| --- | --- | --- | --- | --- | --- |
| 2/23 | Baruch 4 | MP / Exodus 3 | Exodus 3:1-12 | Exodus 3:13-22 | Call and assurance; the divine name and instructions to the elders. |
| 2/24 | Baruch 5 | MP / Acts 1:15-26 | Acts 1:15-20 | Acts 1:21-26 | Judas and the scriptural warrant; qualifications and election of Matthias. Short donor; EP begins with a consequential So. |
| 7/4 | Susanna 1-64 | MP / Judges 15 | Judges 15:1-8 | Judges 15:9-20 | Personal retaliation ends at Etam; Judah hands Samson over and the deliverance at Lehi follows. |
| 10/9 | I Maccabees 1 | MP / II Chronicles 20 | II Chronicles 20:1-19 | II Chronicles 20:20-37 | Prayer, prophetic assurance and worship; the next morning battle and aftermath. |
| 10/10 | I Maccabees 2 | MP / II Kings 1 | II Kings 1:1-8 | II Kings 1:9-18 | Ahaziah recognizes Elijah; the three captains and fulfillment of the oracle. |
| 10/11 | II Maccabees 6 | MP / II Kings 2 | II Kings 2:1-14 | II Kings 2:15-25 | Elijah departs and Elisha takes the mantle; public recognition and early acts of Elisha. |
| 10/12 | II Maccabees 7 | MP / II Kings 3 | II Kings 3:1-20 | II Kings 3:21-27 | Campaign and Elisha’s promise of water; Moab’s response and the battle. |
| 10/13 | II Maccabees 8 | MP / II Kings 4 | II Kings 4:1-17 | II Kings 4:18-44 | Widow’s oil and promised son; death, restoration and food miracles. Short form separates promised birth from restoration. |
| 10/14 | II Maccabees 10 | MP / II Kings 5 | II Kings 5:1-19 | II Kings 5:20-27 | Naaman’s healing, confession and farewell; Gehazi’s deceit and punishment. Verse 19 includes a transitional clause; keep the whole verse. |
| 10/15 | I Maccabees 7 | MP / II Kings 6 | II Kings 6:1-23 | II Kings 6:24-33 | Axe head and captured army released; a new siege of Samaria. Short form uses the axe-head episode as MP and retains the printed opening of the siege in EP; its ending is already abrupt. |
| 10/16 | I Maccabees 9 | MP / II Kings 7 | II Kings 7:1-8 | II Kings 7:9-20 | Promise and discovery of the abandoned camp; reporting the news and fulfillment. |
| 10/17 | I Maccabees 13 | MP / II Kings 8 | II Kings 8:1-15 | II Kings 8:16-29 | Shunammite’s restoration and Hazael’s accession; Judah’s royal annals. |
| 10/18 | I Maccabees 14 | MP / II John 1-13 | II John 1:1-6 | II John 1:7-13 | Greeting and command to love; warning about deceivers and farewell. Awkward short letter: one printed paragraph spans verses 4–11; the thematic turn at 7 is preferable to splitting the greeting or farewell. |
| 11/13 | Judith 4 | EP / Isaiah 26 | Isaiah 26:1-15 | Isaiah 26:16-21 | Trust, righteousness and the enlarged nation; distress, resurrection and shelter from judgment. |
| 11/14 | Judith 8 | EP / Isaiah 27 | Isaiah 27:1-6 | Isaiah 27:7-13 | Leviathan and the restored vineyard; discipline, ruined city and gathered exiles. |
| 11/15 | Judith 9 | EP / Isaiah 28 | Isaiah 28:1-13 | Isaiah 28:14-29 | Ephraim and unheeding leaders; cornerstone oracle and farming analogy. |
| 11/16 | Judith 10 | EP / Isaiah 29 | Isaiah 29:1-14 | Isaiah 29:15-24 | Siege and spiritual blindness; hidden counsel rebuked and the coming reversal. |
| 11/17 | Judith 11 | EP / Isaiah 30 | Isaiah 30:1-17 | Isaiah 30:18-33 | Egyptian alliance and refusal of rest; grace, restoration and judgment on Assyria. |
| 11/18 | Judith 12 | EP / Isaiah 31 | Isaiah 31:1-5 | Isaiah 31:6-9 | Egypt’s weakness and the Lord’s protection; call to return and Assyria’s fall. Very short but paragraph-complete portions. |
| 11/19 | Judith 13 | EP / Isaiah 32 | Isaiah 32:1-8 | Isaiah 32:9-20 | Righteous king and discernment; warning to complacent women and renewal by the Spirit. |
| 11/20 | Judith 14 | EP / Isaiah 33 | Isaiah 33:1-12 | Isaiah 33:13-24 | Prayer amid devastation and the Lord rising; summons to acknowledge him and vision of the king. |
| 11/21 | Judith 15 | EP / Isaiah 34 | Isaiah 34:1-7 | Isaiah 34:8-17 | Judgment on nations and sacrificial imagery for Edom; desolation and its enduring inhabitants. |
| 11/22 | Judith 16 | EP / Isaiah 35 | Isaiah 35:1-4 | Isaiah 35:5-10 | Desert rejoicing and encouragement; healing and the highway of holiness. Short donor. |
| 11/23 | Sirach 1 | EP / Isaiah 36 | Isaiah 36:1-12 | Isaiah 36:13-22 | First embassy and dispute over language; public speech in Judah’s language and response. |
| 11/24 | Sirach 2 | EP / Isaiah 37 | Isaiah 37:1-20 | Isaiah 37:21-38 | Threats and Hezekiah’s complete prayer; divine answer and Assyria’s defeat. |
| 11/25 | Sirach 4 | EP / Isaiah 38 | Isaiah 38:1-8 | Isaiah 38:9-22 | Illness, prayer and sign; Hezekiah’s thanksgiving and closing narrative. Unequal portions preserve the poem. |
| 11/26 | Sirach 6 | EP / Isaiah 39 | Isaiah 39:1-4 | Isaiah 39:5-8 | Babylonian visitors and Hezekiah’s disclosure; Isaiah’s judgment and Hezekiah’s response. Very short donor. |
| 11/27 | Sirach 7 | EP / Isaiah 40 | Isaiah 40:1-11 | Isaiah 40:12-31 | Comfort, enduring word and shepherd; incomparable Creator and strength for the weary. |
| 11/28 | Sirach 9 | EP / Isaiah 41 | Isaiah 41:1-20 | Isaiah 41:21-29 | The Lord’s sovereignty and help for Israel; trial exposing the idols. |
| 11/29 | Sirach 10 | EP / Isaiah 42 | Isaiah 42:1-17 | Isaiah 42:18-25 | Servant, new song and divine action; Israel’s failure to see and hear. |
| 11/30 | Sirach 11 | EP / Isaiah 43 | Isaiah 43:1-13 | Isaiah 43:14-28 | Redeemed Israel as witness to the only Savior; new exodus and Israel’s sins. |
| 12/1 | Sirach 14 | EP / Isaiah 44 | Isaiah 44:1-20 | Isaiah 44:21-28 | Chosen Israel and extended critique of idol-making; redemption and Cyrus. |
| 12/2 | Sirach 17 | EP / Isaiah 45 | Isaiah 45:1-13 | Isaiah 45:14-25 | Cyrus and the Creator’s purpose; salvation addressed to the nations. |
| 12/3 | Sirach 18 | EP / Isaiah 46 | Isaiah 46:1-7 | Isaiah 46:8-13 | Carried idols contrasted with the God who carries Israel; summons to remember and hear. |
| 12/4 | Sirach 21 | EP / Isaiah 47 | Isaiah 47:1-7 | Isaiah 47:8-15 | Babylon humbled from royal pretensions; false security and powerless sorcery. |
| 12/5 | Sirach 34 | EP / Isaiah 48 | Isaiah 48:1-11 | Isaiah 48:12-22 | Israel’s stubbornness and refining; renewed summons and departure from Babylon. |
| 12/6 | Sirach 38 | EP / Isaiah 49 | Isaiah 49:1-13 | Isaiah 49:14-26 | Servant’s mission and restoration with cosmic praise; Zion’s lament and reassurance. |
| 12/7 | Sirach 39 | EP / Isaiah 50 | Isaiah 50:1-3 | Isaiah 50:4-11 | Israel’s alienation and the Lord’s power; obedient servant and invitation to trust. Unequal portions preserve the servant’s speech. |
| 12/8 | Sirach 44 | EP / Isaiah 51 | Isaiah 51:1-11 | Isaiah 51:12-23 | Calls to listen and plea for the Lord’s arm; divine comfort and removal of wrath’s cup. |
| 12/9 | Sirach 45 | EP / Isaiah 52 | Isaiah 52:1-12 | Isaiah 52:13-15 | Zion’s liberation and departure; the servant’s exaltation. Deliberately unequal: verses 13–15 start the servant poem continued in chapter 53. |
| 12/10 | Sirach 46 | EP / Isaiah 53 | Isaiah 53:1-6 | Isaiah 53:7-12 | Misjudgment and bearing our sins; suffering, death and vindication. Awkward division of a unified servant poem, at a stanza boundary. |
| 12/11 | Sirach 47 | EP / Isaiah 54 | Isaiah 54:1-10 | Isaiah 54:11-17 | Barren Zion and covenant of peace; rebuilt city and protection. |
| 12/12 | Sirach 48 | EP / Isaiah 55 | Isaiah 55:1-5 | Isaiah 55:6-13 | Invitation and covenant; call to seek the Lord, effective word and joyful return. |
| 12/13 | Sirach 49 | EP / Isaiah 56 | Isaiah 56:1-8 | Isaiah 56:9-12 | Welcome for eunuchs and foreigners; indictment of irresponsible leaders. |
| 12/14 | Sirach 50 | EP / Isaiah 57 | Isaiah 57:1-13 | Isaiah 57:14-21 | Futile idolatry; comfort for the contrite. |
| 12/15 | Sirach 51 | EP / Isaiah 58 | Isaiah 58:1-5 | Isaiah 58:6-14 | False fasting exposed; true fasting and Sabbath delight. |
| 12/16 | Wisdom 1 | EP / Isaiah 59 | Isaiah 59:1-13 | Isaiah 59:14-21 | Accusation and confession; failed justice and divine intervention. Verse 15 crosses a paragraph; retain it whole in EP. |
| 12/17 | Wisdom 2 | EP / Isaiah 60 | Isaiah 60:1-9 | Isaiah 60:10-22 | Light and returning children and wealth; restored city and everlasting light. |
| 12/18 | Wisdom 3 | EP / Isaiah 61 | Isaiah 61:1-7 | Isaiah 61:8-11 | Anointed mission and restoration; the Lord’s covenant and thanksgiving. |
| 12/19 | Wisdom 4 | EP / Isaiah 62 | Isaiah 62:1-5 | Isaiah 62:6-12 | Zion’s new name and marriage imagery; watchmen and prepared highway. |
| 12/20 | Wisdom 5 | EP / Isaiah 63 | Isaiah 63:1-6 | Isaiah 63:7-19 | The warrior’s vengeance; remembered mercy and prayer. |
| 12/22 | Wisdom 6 | EP / Isaiah 65 | Isaiah 65:1-16 | Isaiah 65:17-25 | Judgment and distinction between servants and rebels; new heavens and earth. |
| 12/23 | Wisdom 7 | EP / Isaiah 66 | Isaiah 66:1-14 | Isaiah 66:15-24 | True worship and Jerusalem’s rebirth; final judgment and gathering of nations. |
| 12/24 | Wisdom 8 | EP / Song of Songs 1 | Song of Songs 1:1-7 | Song of Songs 1:8-17 | Bride’s longing and question about the flock; reply and mutual admiration. |
| 12/29 | Wisdom 9 | EP / Song of Songs 6 | Song of Songs 6:1-3 | Song of Songs 6:4-13 | Search and garden reply; praise of the beloved and return. Unequal portions preserve the exchange. |
| 12/30 | Wisdom 10 | EP / Song of Songs 7 | Song of Songs 7:1-9 | Song of Songs 7:10-13 | Praise of the beloved; her response and invitation. Verse 9 changes speaker internally; keep it whole in MP. |
| 12/31 | Wisdom 11 | EP / Song of Songs 8 | Song of Songs 8:1-7 | Song of Songs 8:8-14 | Longing and love’s enduring seal; little sister, vineyard and final exchange. |

Printed abbreviated donors are divided separately as follows, with complete coverage of the printed abbreviated ranges:

| Date | Abbreviated donor | Morning | Evening |
| --- | --- | --- | --- |
| 10/13 | II Kings 4:8-37 | II Kings 4:8-17 | II Kings 4:18-37 |
| 10/15 | II Kings 6:1-24 | II Kings 6:1-7 | II Kings 6:8-24 |
| 10/17 | II Kings 8:1-19, 25-27 | II Kings 8:1-15 | II Kings 8:16-19,25-27 |

Validation in the remote cloud environment: `DEBUG=False python site/manage.py test
 office.test_alternate_readings office.tests office.test_audio_text
 office.test_audio_ceremony --noinput` exercises migration history, unchanged defaults,
opt-in, both donor directions, AP/DC, odd/even two-year mode, full/abbreviated selection,
translation fallback, Eucharistic precedence, missing/stale data and text/audio identity.
A populated-database audit verified all 57 mappings, 836 populated split translation
fields and 6,156 replacement resolutions; normalized full/abbreviated split text
concatenates to each donor exactly. The seed added 112 Scripture rows and reused the
remaining matching ranges; rerunning it preserved 57 mappings. Django system and
migration-drift checks passed. Offline Node checks covered settings metadata/search
and old/new share-link decoding/round trips; cached Prettier and a supplemental
ESLint recommended-rules check passed for the changed JavaScript. Full Vitest,
repository ESLint and app build/UI checks remain blocked by unavailable frontend
dependencies/private Font Awesome authentication. The required repository pre-commit
run passes its backend hooks; its ESLint hook cannot resolve `globals` from the app
configuration. No authenticated npm installation or `.npmrc` token inspection was
performed. These checks must be completed in an authorized frontend environment
before merging or deployment.
