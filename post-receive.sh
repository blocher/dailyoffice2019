#!/bin/sh

echo "======Making Directory======"
mkdir -p /var/www/api.dailyoffice2019.com/
cd /var/www/api.dailyoffice2019.com/

echo "======Checking out code======"
git --work-tree=/var/www/api.dailyoffice2019.com --git-dir=/var/repo/api.dailyoffice2019.com/ checkout -f vue-test

echo "======Making and activating venv======"
sudo rm -rf env
python3.13 -m venv env
. env/bin/activate
cd site

# echo "======Installing C Bindings======"
# pip install wheel
# CFLAGS="-Wno-narrowing" pip install cld2-cffi  --no-cache-dir

echo "======Installing Requirements======"
pip install -r requirements.txt --no-cache-dir

echo "======Installing Yarn Requirements and updating browserslist======"
rm -rf node_modules
npm install
yes | npx update-browserslist-db@latest

echo "======Migrating Database======"
python3.13 manage.py migrate --no-input

echo "======Collecting Static Files======"
# enable corepack
#mkdir -p static
#npx webpack
python3.13 manage.py collectstatic --noinput --clear

echo "======Clearing Memcached======"
echo "flush_all" | nc -q 2 localhost 11211

echo "======Clearing Python Cache======"
sudo find . -name "*.pyc" -exec rm -f {} \;
sudo find . -name "*.pyo" -exec rm -f {} \;

echo "======Restarting Uvicorn with Systemctl======"
systemctl stop dailyoffice
systemctl start dailyoffice
# systemctl status dailyoffice

echo "======Reclearing Memcached======"
echo "flush_all" | nc -q 2 localhost 11211

echo "======Clearing Python Cache and Recompiling======"
sudo find . -name "*.pyc" -exec rm -f {} \;
sudo find . -name "*.pyo" -exec rm -f {} \;
python -m compileall .

echo "======Enabling Kronos cron-tasks======"
python3.13 manage.py installtasks
