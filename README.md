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

- Python 3.12 or newer (Django 6.1 supports Python 3.12–3.14)
- Node 22.22.2+ within Node 22, or Node 24.15.0+; Node 24 LTS is recommended
- PostgreSQL
- Memcached 1.6

The project is known to work with these versions, although it may also work with more recent versions.

### Dependency refresh (October 11, 2026)

Project-owned manifests were checked against PyPI, npm (including the authenticated Font Awesome registry),
and upstream pre-commit releases. Existing `>=`, `^`, and exact-version conventions are retained;
these ranges do not freeze future releases. The three existing npm lockfiles are refreshed together.
The email-template package has no dependencies. Vendored `node_modules` manifests are not source manifests.

Compatibility exceptions:

- TypeScript is updated to 6.0.3. Latest stable 7.0.2 exceeds `@typescript-eslint/parser` 8.71.1's
  declared `>=4.8.4 <6.1.0` peer range. Upgrade TypeScript 7 only after the lint parser supports it.
- Firebase stays on the newest 12.x release, 12.19.0. Latest stable 13.0.0 conflicts with
  `@capacitor-firebase/analytics` 8.5.2's `firebase ^12.6.0` peer requirement.
- `@achrinza/node-ipc` stays at 10.1.11: npm's `latest` tag points to the older 9.2.10 line.
- `vue-meta` stays at 3.0.0-alpha.10: its stable `latest` tag, 2.4.0, targets Vue 2 rather than this Vue 3 app.
- The three Git requirements retain their existing fork/branch references. They are moving references,
  not numbered PyPI releases; the `django-inlinecss@django4` fork must not be replaced with the old PyPI package.
- Commented-out pre-commit hooks are inactive and are not treated as installed dependencies.

Breaking changes and migration checks:

- **Django 5.2 → 6.1:** Python 3.12+ is required; check PostgreSQL/server support, third-party admin widgets,
  and removed APIs. Django 6.0 removes `CheckConstraint(check=...)`, argument-free `format_html()`,
  and positional `Model.save()` arguments. Django 6.1 changes some admin template blocks and markup.
  See [6.0 release notes](https://docs.djangoproject.com/en/6.1/releases/6.0/) and
  [6.1 release notes](https://docs.djangoproject.com/en/6.1/releases/6.1/).
  `site/runtime.txt` still declares Python 3.7 and the historical `site/deploy/post-receive` creates a
  Python 3.10 environment: neither can install these requirements. Provision a supported interpreter
  before using those deployment paths; this refresh does not deploy or change server configuration.
- **Vite 7 → 8:** the production bundler changes from Rollup to Rolldown; build output, plugins,
  minification, and chunking need checking. See the [migration guide](https://vite.dev/guide/migration.html).
- **Vitest 3 → 5 / jsdom 27 → 30:** review mocks, timers, DOM behavior, and test-runner configuration.
  Vitest 5 clears mock calls before each test by default and authenticates the UI URL.
  See the [migration guide](https://vitest.dev/guide/migration/).
- **ESLint 9 → 10 and lint-plugin majors:** config lookup and recommended rules change.
  The hook now installs the actual app-config imports and their required peers. The unused TSLint
  bridge was removed from the hook because it only supports ESLint 8.
  See the [migration guide](https://eslint.org/docs/latest/use/migrate-to-10.0.0).
- **Babel 7 → 8 / webpack tooling majors:** Babel 8 raises Node requirements, is ESM-only, and removes
  deprecated options. Legacy loaders/plugins need checking if the old pipeline is used again.
  See the [Babel guide](https://babeljs.io/docs/v8-migration).
- **Legacy Capacitor 6 → 8:** native projects need platform migrations and `cap sync` before rebuilding;
  lockfile updates alone do not migrate Xcode, Android Gradle, or SDK requirements.
  The active Vue app already used Capacitor 8. See the [Capacitor guide](https://capacitorjs.com/docs/updating/8-0).
- **MJML 4 → 5, iCalendar 6 → 7, OpenAI 2 → 3, Pillow 11 → 12, Delorean 1 → 2,
  cryptography 46 → 50 and pyOpenSSL 25 → 26:** treat email rendering, calendar serialization,
  audio-provider calls, image operations, time-zone conversions, and TLS integrations as migration
  surfaces. Major-version changes are flagged below; a major number alone does not prove a specific
  application failure, and automated checks do not cover live external services or native builds.
- **Black 25 → 26:** formatting output can change. Hook and Python requirement now use the same release.

The inventory below flags every changed first version component, including calendar-versioned projects
(such as Black, django-filter, pipenv, and pytz). These are review flags, not a claim that each package
has an application-breaking change. Pre-1.0 updates (`decode-uri-component`, `django-environ`, Python `mjml`,
Hypercorn, and uvicorn) also warrant review despite their unchanged first component.

| Manifest | Dependency | Previous | Updated |
| --- | --- | --- | --- |
| `app/package.json` | `nanoid` | `^5.1.6` | `6.0.2` |
| `app/package.json` | `npm` | `^11.10.0` | `12.2.0` |
| `app/package.json` | `unplugin-vue-components` | `^31.0.0` | `32.1.0` |
| `app/package.json` | `@babel/eslint-parser` | `^7.28.4` | `8.0.7` |
| `app/package.json` | `@cypress/request` | `^3.0.9` | `4.0.1` |
| `app/package.json` | `@eslint/js` | `^9.36.0` | `10.0.1` |
| `app/package.json` | `@vitest/ui` | `^3.2.4` | `5.0.3` |
| `app/package.json` | `cypress` | `^15.3.0` | `16.1.1` |
| `app/package.json` | `eslint` | `^9.36.0` | `10.12.0` |
| `app/package.json` | `eslint-plugin-cypress` | `^5.1.1` | `7.0.2` |
| `app/package.json` | `eslint-plugin-vue-scoped-css` | `^2.12.0` | `3.1.3` |
| `app/package.json` | `globals` | `^16.4.0` | `17.13.0` |
| `app/package.json` | `jsdom` | `^27.0.0` | `30.1.2` |
| `app/package.json` | `npm` | `^11` | `12.2.0` |
| `app/package.json` | `typescript` | `^5.9.3` | `6.0.3` |
| `app/package.json` | `vite` | `^7.1.7` | `8.3.4` |
| `app/package.json` | `vitest` | `^3.2.4` | `5.0.3` |
| `site/package.json` | `@babel/core` | `^7.26.0` | `8.0.7` |
| `site/package.json` | `@babel/preset-env` | `^7.26.0` | `8.0.7` |
| `site/package.json` | `@capacitor-community/firebase-analytics` | `^6.0.0` | `8.1.0` |
| `site/package.json` | `@capacitor/android` | `^6.2.0` | `8.5.3` |
| `site/package.json` | `@capacitor/app` | `^6.0.2` | `8.1.2` |
| `site/package.json` | `@capacitor/core` | `^6.2.0` | `8.5.3` |
| `site/package.json` | `@capacitor/ios` | `^6.2.0` | `8.5.3` |
| `site/package.json` | `@capacitor/preferences` | `^6.0.3` | `8.0.1` |
| `site/package.json` | `@capacitor/splash-screen` | `^6.0.3` | `8.0.2` |
| `site/package.json` | `@capacitor/status-bar` | `^6.0.2` | `8.0.4` |
| `site/package.json` | `babel-loader` | `^9.2.1` | `10.1.1` |
| `site/package.json` | `copy-webpack-plugin` | `^12.0.2` | `14.0.0` |
| `site/package.json` | `mjml` | `^4.15.3` | `5.4.1` |
| `site/package.json` | `nanoid` | `^5.0.9` | `6.0.2` |
| `site/package.json` | `postcss-preset-env` | `^10.1.2` | `11.6.1` |
| `site/package.json` | `sass-loader` | `^16.0.4` | `17.0.1` |
| `site/package.json` | `webpack-cli` | `^6.0.1` | `7.2.3` |
| `site/package.json` | `webpack-dev-server` | `^5.2.0` | `6.0.0` |
| `site/package.json` | `@capacitor/cli` | `^6.2.0` | `8.5.3` |
| `site/requirements.txt` | `black` | `25.9.0` | `26.10.1` |
| `site/requirements.txt` | `cryptography` | `46.0.2` | `50.0.2` |
| `site/requirements.txt` | `Delorean` | `1.0.0` | `2.0.0` |
| `site/requirements.txt` | `Django` | `5.2.6` | `6.1.2` |
| `site/requirements.txt` | `django-debug-toolbar` | `6.0.0` | `8.0.0` |
| `site/requirements.txt` | `django-distill` | `3.2.7` | `4.0.6` |
| `site/requirements.txt` | `django-filter` | `25.1` | `26.2` |
| `site/requirements.txt` | `django-js-asset` | `3.1.2` | `4.2.0` |
| `site/requirements.txt` | `django_tinymce` | `4.1.0` | `5.0.0` |
| `site/requirements.txt` | `gunicorn` | `23.0.0` | `26.2.0` |
| `site/requirements.txt` | `icalendar` | `6.3.1` | `7.3.0` |
| `site/requirements.txt` | `openai` | `2.0.0` | `3.29.0` |
| `site/requirements.txt` | `Pillow` | `11.3.0` | `12.3.0` |
| `site/requirements.txt` | `pip` | `25.2` | `26.2.1` |
| `site/requirements.txt` | `pipdeptree` | `2.28.0` | `4.2.7` |
| `site/requirements.txt` | `pipenv` | `2025.0.4` | `2026.9.0` |
| `site/requirements.txt` | `pyOpenSSL` | `25.3.0` | `26.4.0` |
| `site/requirements.txt` | `pytz` | `2025.2` | `2026.5` |
| `site/requirements.txt` | `setuptools` | `80.9.0` | `84.0.0` |
| `site/requirements.txt` | `virtualenv` | `20.34.0` | `21.14.6` |

Validation with Python 3.14.2 and Node 24.21.0:

- All Python requirements install in a clean temporary environment; `pip check` reports no broken requirements.
- Django system checks and all 220 backend tests (`office`, `patrons`, `churchcal`, `bible`, `psalter`) pass.
  Four pre-existing failures were resolved: patron message endpoints now share one local-date snapshot
  to keep their dates and labels consistent across midnight; the custom error page returns HTTP 404;
  deuterocanonical audio tests mock dialogue clips as well as reading clips and verify the introduction,
  both reading paragraphs, and closing. The missing narration was an unmocked-provider test issue.
- Upgrading debug-toolbar exposed routes being imported while its app is excluded during tests.
  URL registration now checks that the app is installed, with a regression test.
- Vue production build passes and all 53 tests across 10 files pass on Vite 8 / Vitest 5.
  Build warnings remain for large chunks and `vue-axios` using CommonJS `module` inside its ESM bundle.
- ESLint 10 successfully checks `app/src/helpers/clientId.test.js` with the current config.
- Node 24 emits engine warnings from old `node-ipc` dependencies, including a transitive 9.x dependency
  of the legacy Vue CLI Capacitor plugin. These old dependencies need a separate native-tooling cleanup.
- Native iOS/Android/Electron builds, Cypress browser tests, live AI/TLS provider requests, and the unused
  legacy webpack/email pipeline have not been exercised. Successful web checks do not establish those paths' compatibility.
- Clean `npm ci --ignore-scripts` installs pass for the root, Vue app, and legacy manifests.
  The updated `pre-commit run` passes, and the ESLint hook also passes when explicitly exercised
  on the existing frontend test file. Dependency lifecycle scripts were skipped during temporary installation.

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
