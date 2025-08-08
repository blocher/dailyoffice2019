# Daily Office 2019 - Developer Instructions

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Project Overview

Daily Office 2019 is a Django + Vue.js web application for Christian daily prayer services. The project generates a static site from dynamic content and deploys to dailyoffice2019.com.

**Architecture:**
- **Backend**: Django 5.1+ in `/site/` directory with PostgreSQL database
- **Frontend**: Vue 3 + Vite in `/app/` directory with TypeScript support  
- **Mobile**: Capacitor for iOS/Android apps
- **Deployment**: Static site generation via django-distill

## Critical Setup Requirements

### Prerequisites - Install These First
- Python 3.12
- Node.js 16+ (tested with Node 20)
- PostgreSQL 13+
- Memcached 1.6+

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y postgresql memcached python3-venv python3-pip
```

## Working Effectively

### Bootstrap Environment - ALWAYS Do This First
```bash
# 1. Set up environment files
cp app/.env.development app/.env.local
cp site/website/.env.example site/website/.env

# 2. Edit site/website/.env - Set ALL required environment variables
# Add development values for all missing variables:
DEBUG=True
SECRET_KEY=development-secret-key-not-for-production
GOOGLE_API_KEY=development-api-key
GOOGLE_CUSTOM_SEARCH_ENGINE_KEY=development-search-key
OPENAI_API_KEY=development-openai-key
# ... (see Complete Environment Setup section below)

# 3. Start required services
sudo service postgresql start
sudo service memcached start
```

### Database Setup - Takes ~4 seconds
```bash
# Create database and user
sudo -u postgres psql -c "CREATE DATABASE dailyoffice;"
sudo -u postgres psql -c "CREATE USER dailyoffice WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dailyoffice TO dailyoffice;"

# Import database dump - Takes 3-4 seconds
unzip -p site/dailyoffice_2024_01_30.sql.zip dailyoffice_2024_01_30.sql | sudo -u postgres psql dailyoffice
```

### Python Environment Setup - NETWORK ISSUES EXPECTED
```bash
cd site
python3 -m venv env
source env/bin/activate

# CRITICAL: Network timeouts are common with PyPI
# NEVER CANCEL: Takes 5-45 minutes when working, use maximum timeouts
pip install --timeout 1200 --retries 10 -r requirements.txt
```

**EXPECTED ISSUE**: `pip install` frequently fails with `ReadTimeoutError` due to network issues. **NEVER CANCEL** - retry with longer timeouts.

**Workaround if pip install fails completely:**
```bash
# Install core dependencies individually with retries
pip install --timeout 600 --retries 5 Django==5.1 psycopg-binary beautifulsoup4 requests arrow django-environ
```

### Backend Node.js Setup - Takes ~2 minutes
```bash
cd site
npm install
# Ignore security warnings - Takes 1.5-2 minutes, NEVER CANCEL
```

### Frontend Setup - NETWORK ISSUES WITH FONTAWESOME
```bash
cd app
npm install
```

**EXPECTED ISSUE**: Fails with `ENOTFOUND npm.fontawesome.com` due to FontAwesome Pro dependencies requiring authentication.

**Current Status**: Frontend build requires FontAwesome Pro access. Document this limitation and contact project maintainers for license setup.

## Build Process - NEVER CANCEL BUILDS

### Backend Django Build
```bash
cd site
source env/bin/activate

# Collect static assets - Takes 30-60 seconds
python manage.py collectstatic --noinput

# Generate static site - Takes 5-45 minutes. NEVER CANCEL.
# Use timeout of 60+ minutes
python manage.py distill-local --force
```

**CRITICAL TIMING**: Static site generation takes 5-45 minutes. **NEVER CANCEL** - Set timeouts to 60+ minutes minimum.

### Using Makefile - Takes 5-45 minutes total
```bash
# Clean and build everything - NEVER CANCEL, use long timeouts
make clean build
```

## Development Servers

### Django API Server
```bash
cd site
source env/bin/activate
python manage.py runsslserver
# Accessible at https://127.0.0.1:8000/
# API docs at https://127.0.0.1:8000/api/
```

**Note**: Requires `django-sslserver` package (part of requirements.txt)

### Frontend Development (When FontAwesome Issues Resolved)
```bash
cd app
npm run dev
# Accessible at http://127.0.0.1:8080
```

## Complete Environment Setup

**CRITICAL**: The .env file requires ALL these variables for Django to start:

```bash
# Edit site/website/.env with ALL these development values:
DEBUG=True
DEBUG_DATES=False
SECURE_SSL_REDIRECT=False
SECURE_PROXY_SSL_HEADER=http
GOOGLE_API_KEY=development-api-key
GOOGLE_CUSTOM_SEARCH_ENGINE_KEY=development-search-key
POSTGRES_NAME=dailyoffice
POSTGRES_USER=dailyoffice
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
SECRET_KEY=development-secret-key-not-for-production
FIRST_BEGINNING_YEAR=2018
LAST_BEGINNING_YEAR=2021
FIRST_BEGINNING_YEAR_APP=2019
LAST_BEGINNING_YEAR_APP=2020
BUGSNAG_KEY=development-bugsnag-key
MAILGUN_PUBLIC_KEY=development-mailgun-public
MAILGUN_PRIVATE_KEY=development-mailgun-private
MAILGUN_SMTP_PASSWORD=development-mailgun-smtp
MJML_APPLICATION_ID=development-mjml-app
MJML_PUBLIC_KEY=development-mjml-public
MJML_SECRET_KEY=development-mjml-secret
EMAIL_HOST=smtp.gmail.com
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_PORT=465
EMAIL_HOST_USER=development@example.com
EMAIL_HOST_PASSWORD=development-email-password
ZOOM_LINK=https://zoom.us/development
SITE_ADDRESS=https://127.0.0.1:8000
OMDB_API_KEY=development-omdb-key
UTELLY_API_KEY=development-utelly-key
IMDB_API_KEY=development-imdb-key
YOUTUBE_API_KEY=development-youtube-key
MAILCHIMP_API_KEY=development-mailchimp-key
MAILCHIMP_PREFIX=us4
MAILCHIMP_LIST_ID=development-list-id
OPENAI_API_KEY=development-openai-key
```

## Testing and Validation

### Django System Check
```bash
cd site
source env/bin/activate
python manage.py check
```

### Code Formatting - ALWAYS Run Before Committing
```bash
# Python formatting from site/ directory
find . -iname "*.py" | xargs black --target-version=py313 --line-length=119

# Pre-commit hooks for all formatting
pre-commit run --all-files
```

### Linting
```bash
# Frontend linting (when npm install works)
cd app
npm run lint

# Python linting via pre-commit
pre-commit run --all-files
```

## Known Issues and Workarounds

### Network Timeouts - CRITICAL TIMING ISSUES
- **PyPI timeouts**: Use `--timeout 1200 --retries 10` with pip
- **FontAwesome Pro**: Frontend requires authentication to npm.fontawesome.com
- **Build timeouts**: Static generation takes 5-45 minutes, **NEVER CANCEL**
- **Solution**: Always use maximum timeouts (60+ minutes) and multiple retries

### Build Times and Timeout Requirements
- **Database import**: ~4 seconds (fast and reliable)
- **Backend npm install**: ~2 minutes
- **Python pip install**: 5-45 minutes (network dependent, **NEVER CANCEL**)
- **Static site generation**: 5-45 minutes (**NEVER CANCEL**, use 60+ minute timeouts)
- **collectstatic**: 30-60 seconds

### Authentication Issues
- **PostgreSQL**: Use postgres user for database import
- **FontAwesome**: Requires Pro license authentication for frontend builds

## Validation Scenarios

After making changes, ALWAYS test these scenarios:

1. **Test Django setup**:
   ```bash
   cd site && source env/bin/activate && python manage.py check
   ```

2. **Test static site generation** (LONG RUNNING - 5-45 minutes):
   ```bash
   cd site && source env/bin/activate && python manage.py distill-local --force
   ```

3. **Run formatting**:
   ```bash
   black --target-version=py313 --line-length=119 .
   ```

4. **Test database connectivity**:
   ```bash
   python manage.py migrate --check
   ```

5. **Test development server**:
   ```bash
   python manage.py runsslserver
   # Verify https://127.0.0.1:8000/ loads
   ```

## Project Structure Reference

### Key Directories
```
/site/          - Django backend application
  /website/     - Main Django app with settings
  /office/      - Daily Office generation logic  
  /churchcal/   - Church calendar calculations
  /bible/       - Bible passage retrieval
  /psalter/     - Psalm passage handling
  
/app/           - Vue.js frontend application
  /src/         - Vue component source code
  
/static_export/ - Generated static site output
```

### Django Apps Overview
- **website**: Base site configuration, settings, URLs
- **office**: Core daily office generation and logic
- **churchcal**: Anglican/Episcopal church calendar support
- **bible**: Bible Gateway API integration
- **psalter**: Coverdale Psalms from BCP 2019

### Build Output
- Static site exports to `/static_export/`
- Deployable to Netlify or static hosts
- No server requirements for final site

## Common Commands Reference

```bash
# Environment setup
source site/env/bin/activate

# Development server
python site/manage.py runsslserver

# Static generation (5-45 minutes, NEVER CANCEL)
python site/manage.py distill-local --force

# Code formatting
find site -iname "*.py" | xargs black --target-version=py313 --line-length=119

# Database operations
python site/manage.py migrate
python site/manage.py collectstatic

# Build everything (5-45 minutes total, NEVER CANCEL)
make clean build
```

## Troubleshooting Network Issues

If you encounter persistent network timeouts:

1. **For Python packages**: Use maximum timeouts and retries, install core packages individually
2. **For FontAwesome**: Contact project maintainers for Pro license setup
3. **For builds**: Use maximum timeouts (60+ minutes) and **NEVER CANCEL**
4. **For database**: Import works reliably and is fast (~4 seconds)

**NEVER CANCEL RULE**: If any build process is running for less than 60 minutes, do not cancel it. The project has complex dependency chains that require patience.

Always validate that basic Django functionality works with proper environment setup before attempting full builds.