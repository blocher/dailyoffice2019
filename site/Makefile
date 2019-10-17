python=/usr/bin/env python

all: clean build

build:
	mkdir -p static
	mkdir -p public
	pip install -r requirements.txt
	$(python) manage.py collectstatic --noinput
	$(python) manage.py distill-local --force

clean:
	rm -rf public
	rm -rf static
