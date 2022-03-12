.PHONY: clean wheel install tests check_version dist check_dist upload_test upload bump release create-release docker docker_upload

PYCACHE := $(shell find . -name '__pycache__')
EGGS := $(wildcard *.egg-info)
CURRENT_VERSION := $(shell awk '/current_version/ {print $$3}' setup.cfg)

clean:
	@echo "=> Cleaning"
	@rm -fr build dist $(EGGS) $(PYCACHE)


prepare: clean
	git add .
	git status
	git commit -m "cleanup before release"

# Version commands

bump:
ifdef part
ifdef version
	bumpversion --new-version $(version) $(part) && grep current setup.cfg
else
	bumpversion --allow-dirty $(part) && grep current setup.cfg
endif
else
	@echo "Provide part=major|minor|patch|release|build and optionally version=x.y.z..."
	exit 1
endif

# Dist commands

dist:
	@rm -f dist/*
	@python setup.py sdist bdist_wheel

release:
	git add .
	git status
	git diff-index --quiet HEAD || git commit -m "Latest release: $(CURRENT_VERSION)"
	git tag -a v$(CURRENT_VERSION) -m "Latest release: $(CURRENT_VERSION)"

create-release:
	@github-release release -u bernhard-42 -r cadquery-massembly -t v$(CURRENT_VERSION) -n cadquery-massembly-$(CURRENT_VERSION)
	@sleep 2
	@github-release upload  -u bernhard-42 -r cadquery-massembly -t v$(CURRENT_VERSION) -n cadquery_massembly-$(CURRENT_VERSION).tar.gz -f dist/cadquery_massembly-$(CURRENT_VERSION).tar.gz

install: dist
	@echo "=> Installing cadquery_massembly"
	@pip install --upgrade .

check_dist:
	@twine check dist/*

upload:
	@twine upload dist/*