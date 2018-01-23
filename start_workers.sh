#!/usr/bin/env bash

celery worker -A bf.app.celery --loglevel=INFO --prefetch-multiplier=25 --concurrency=20 -n v2-1@%h &
celery worker  -A bf.app.celery --loglevel=INFO -Q search -n search-worker-1@%h &
flower -A bf.app.celery --url_prefix=flower &