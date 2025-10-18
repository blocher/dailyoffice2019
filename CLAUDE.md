# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Daily Office 2019 (https://www.dailyoffice2019.com) is a Django application that generates a static website for praying the Daily Office according to The Book of Common Prayer (2019) of the Anglican Church in North America. The project consists of:

- **Backend (Django)**: Located in `/site`, generates Office content via API and static site generation
- **Frontend (Vue 3)**: Located in `/app`, a Vue 3 + Vite SPA that consumes the Django API
- **Mobile Apps**: Capacitor-based iOS and Android apps built from the frontend

The application generates morning, midday, evening, and compline prayers for any date, with automatic scripture readings, psalms, and collects based on the church calendar.

## Development Setup Commands

### Backend (Django) - `/site` directory

**Initial setup:**
```bash
# Create virtual environment
python3 -m venv env
source env/bin/activate  # Load environment

# Install dependencies
pip install -r requirements.txt

# Setup environment files
cp website/.env.example website/.env
# Edit website/.env with database credentials

# Database setup (one-time)
createdb dailyoffice
psql -d postgres -c "create user dailyoffice with password 'password';"
psql -d postgres -c "grant all privileges on database dailyoffice to dailyoffice;"
unzip -p dailyoffice_2024_01_30.sql.zip dailyoffice_2024_01_30.sql | psql -U dailyoffice dailyoffice
```

**Common commands:**
```bash
# Activate virtual environment (always run first)
source env/bin/activate

# Run development server (with SSL)
python manage.py runsslserver
# API docs accessible at https://127.0.0.1:8000/api/

# Run standard development server
python manage.py runserver

# Collect static files
python manage.py collectstatic

# Build static site for deployment
make build  # Runs collectstatic + distill-local

# Clean build artifacts
make clean
```

**Django management commands:**
```bash
# Church calendar imports
python manage.py import_all  # Import all church calendar data
python manage.py import_temporale
python manage.py import_sanctorale_based
python manage.py import_propers
python manage.py generate_ics_calendars

# Database migrations
python manage.py makemigrations
python manage.py migrate
```

### Frontend (Vue 3) - `/app` directory

**Setup:**
```bash
npm install

# Setup environment files
cp .env.development .env.local
```

**Common commands:**
```bash
# Development server (hot reload)
npm run dev
# Accessible at http://127.0.0.1:8080

# Production build
npm run build

# Preview production build
npm run serve

# Run unit tests
npm run test:unit

# Run e2e tests (Cypress)
npm run test:e2e
npm run test:e2e:open  # Interactive mode

# Linting
npm run lint

# iOS build and run
npm run ios  # Builds, syncs, and runs on iOS
npx cap sync  # Sync web assets to native projects
```

## Architecture

### Backend Django Apps

The Django project is organized into specialized apps:

- **website** (`site/website/`): Base Django configuration
  - `settings.py`: All Django settings and installed apps
  - `urls.py`: Root URL routing (not `routes.py` despite README mention)
  - `api_urls.py`: API endpoint definitions

- **office** (`site/office/`): Core Office generation logic
  - `offices.py`: Base `Office` class that all offices inherit from
  - `morning_prayer.py`: Morning Prayer office implementation
  - `evening_prayer.py`: Evening Prayer office implementation
  - `midday_prayer.py`: Midday Prayer implementation
  - `compline.py`: Compline (bedtime prayer) implementation
  - `family_*.py`: Family prayer services
  - `models.py`: Office-related database models (StandardOfficeDay, HolyDayOfficeDay, ThirtyDayPsalterDay)
  - `views.py`: API views for office content
  - `canticles.py`: Canticle (songs/hymns) management

- **churchcal** (`site/churchcal/`): Church calendar calculations
  - `calculations.py`: Date calculations for liturgical calendar (31KB - complex logic)
  - `models.py`: Feast days, commemorations, calendar models
  - `management/commands/`: Import scripts for calendar data

- **bible** (`site/bible/`): Scripture passage retrieval
  - `sources.py`: Bible API integrations (currently Bible Gateway)
  - `passage.py`: Passage parsing and formatting

- **psalter** (`site/psalter/`): Psalm retrieval (Coverdale translation from BCP 2019)

### Office Generation Pattern

Each Office type (MorningPrayer, EveningPrayer, etc.) inherits from the base `Office` class:

1. `Office.__init__(date)` calls `get_calendar_date(date)` to determine liturgical calendar position
2. Loads appropriate readings from `HolyDayOfficeDay` or `StandardOfficeDay` based on feast vs. ordinary day
3. Each office is composed of modular `OfficeSection` subclasses (e.g., `ComplineOpening`, `MorningPrayerPsalms`)
4. The `modules` list on each Office class defines which sections render in order

### Frontend Architecture (Vue 3)

The frontend (`app/src/`) is a modern Vue 3 SPA:

- **Router** (`src/router/`): Vue Router 4 with routes for:
  - `/readings/` - Daily readings
  - `/calendar/` - Church calendar view
  - `/pray/` - Office prayer interface
  - `/commemoration/` - Saint/feast day information

- **State Management** (`src/store/`): Vuex store for application state

- **Components** (`src/components/`):
  - `Office*.vue` - Office display components (OfficeLeader, OfficeCongregation, etc.)
  - `AudioPlayer.vue` - Audio playback for prayers
  - `MenuTailwind.vue` - Main navigation
  - `CalendarCard.vue` - Calendar display
  - `CollectsFilters.vue` - Collect browsing

- **Views** (`src/views/`): Page-level components

- **Styling**: Tailwind CSS 4.x with custom configuration

### Mobile Apps (Capacitor)

Native iOS and Android apps use Capacitor 7.x to wrap the Vue frontend:

- Firebase Analytics integrated for native platforms (`@capacitor-firebase/analytics`)
- Platform-specific configuration in `android/` and `ios/`
- Sync web build to native projects: `npx cap sync`

### Static Site Generation

The project uses `django-distill` to generate a static site from Django:

1. `python manage.py collectstatic` - Gathers static assets
2. `python manage.py distill-local --force` - Generates static HTML
3. Output goes to `public/` directory
4. Deployed to Netlify (config in `netlify.toml`) with redirects from `/office/*` to `/:splat`

## Code Formatting

### Python (Backend)
- Use `black` with line length 119, target Python 3.13
- Pre-commit hooks configured in `.pre-commit-config.yaml`
- Format command from `site/` directory:
  ```bash
  find . -iname "*.py" | xargs black --target-version=py313 --line-length=119
  ```

### JavaScript/Vue (Frontend)
- ESLint + Prettier configured
- Pre-commit hooks run on `app/src/` files
- Lint command: `npm run lint` (in `app/` directory)

## Key Technical Details

### Database
- PostgreSQL required
- Database name: `dailyoffice`
- Memcached 1.6 for caching (optional but recommended)

### Environment Variables
- Backend: `site/website/.env` (copy from `.env.example`)
- Frontend: `app/.env.local` (copy from `.env.development` or `.env.production`)
- Critical backend vars: `DEBUG`, `POSTGRES_*`, `SECRET_KEY`, `SITE_ADDRESS`

### Python Dependencies
- Django 5.2.6+
- django-distill for static site generation
- djangorestframework for API
- drf-yasg for API documentation
- beautifulsoup4, lxml for HTML/XML processing
- arrow, Delorean for date handling

### Frontend Dependencies
- Vue 3.5.x with Composition API
- Vite 7.x for build tooling
- Capacitor 7.x for mobile apps
- Element Plus, Headless UI for components
- Axios for API calls
- Vitest for unit testing, Cypress for e2e

### Testing
- Backend: Test files exist (`site/office/tests.py`, etc.) but test coverage is limited per README
- Frontend: Vitest for unit tests (`npm run test:unit`), Cypress for e2e (`npm run test:e2e`)

## Deployment

The site is deployed to Netlify as a static site:
- Build output: `static_export/` (configured in `netlify.toml`)
- Cache headers set to no-cache for dynamic content
- Redirects configured from legacy `/office/*` paths
