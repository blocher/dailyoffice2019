python=/usr/bin/env python

all: clean build

build:
	mkdir -p static
	mkdir -p public
	$(python) manage.py collectstatic --noinput
	$(python) manage.py distill-local --force

clean:
	rm -rf public
	rm -rf static

# Deploy the checked-out commit (must be on origin/master). See deploy/deploy.sh.
.PHONY: deploy deploy-api deploy-web
deploy:
	deploy/deploy.sh all

deploy-api:
	deploy/deploy.sh api

deploy-web:
	deploy/deploy.sh web
