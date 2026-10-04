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
