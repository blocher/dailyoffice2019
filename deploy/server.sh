#!/usr/bin/env bash
# Runs on the production server from the commit being deployed. Called by deploy/deploy.sh over SSH.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Python environment"
[ -d env ] || python3.13 -m venv env
. env/bin/activate
pip install --quiet --no-cache-dir -r site/requirements.txt

cd site

echo "==> Migrating database"
python manage.py migrate --no-input

echo "==> Collecting static files"
python manage.py collectstatic --noinput --clear

echo "==> Restarting app"
systemctl restart dailyoffice
# Memcached is the production cache: this also clears the office API response
# cache and any in-flight audio-build locks (site/office/response_cache.py).
echo "flush_all" | nc -q 2 localhost 11211
# And Cloudflare's copies of API content (site/website/edge_cache.py).
python manage.py clear_office_cache

echo "==> Installing cron tasks"
python manage.py installtasks
