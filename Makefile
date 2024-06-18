SHELL := /bin/bash
.SHELLFLAGS := -O extglob -eo pipefail -c
.DEFAULT_GOAL := html
.SUFFIXES:

index.html: templates/*
	python3 scripts/gen_html.py index.html

media.html: templates/*
	python3 scripts/gen_html.py media.html

.PHONY: debug_ingest
debug_ingest:
# 	touch images/*/*/*.json
	touch images/2024/06/*.json
	python3 scripts/ingest_uploads.py
	ls -lh images/2024/*/thumbnails.jpg


.PHONY: html
html: index.html media.html
