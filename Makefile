VERSION ?= $(shell dunamai from git --style pep440 --format "{base}.dev{distance}+{commit}")

install-dev:
	poetry install --with dev
	pre-commit install

install:
	poetry install

install-prod:
	poetry install --with prod

clean:
	pip uninstall nbdefense
	pip freeze | xargs -n1 pip uninstall -y
	rm -f dist/*

test:
	poetry run pytest

test-watch:
	ptw --ignore ./.tmp

build:
	poetry build

build-prod: version
	poetry build

version:
	echo "__version__ = '$(VERSION)'" > nbdefense/_version.py
	poetry version $(VERSION)

lint: bandit mypy

bandit:
	poetry run bandit -c pyproject.toml -r .

mypy:
	poetry run mypy --ignore-missing-imports --strict --check-untyped-defs .

format:
	black .
