.PHONY: clean clean-test clean-pyc clean-build docs help lint test test-all
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with flake8 and black
	pydocstyle --config=setup.cfg xclim
	flake8 --config=setup.cfg xclim
	black --check --target-version py38 xclim
	black --check --ipynb --target-version py38 docs --include "\.ipynb$$"
	blackdoc --check --target-version py38 xclim --exclude xclim/indices/__init__.py,xclim/docs/installation.rst
	isort --check --settings-file=setup.cfg xclim --add_imports="from __future__ import annotations"
	pylint --rcfile=pylintrc --exit-zero xclim

test: ## run tests quickly with the default Python
	pytest xclim/testing/tests
	pytest --nbval docs/notebooks
	pytest --rootdir xclim/testing/tests/ --xdoctest xclim

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source xclim -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

linkcheck: ## run checks over all external links found throughout the documentation
	rm -f docs/xclim*.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ --private --module-first xclim xclim/testing/tests
	$(MAKE) -C docs clean
	$(MAKE) -C docs linkcheck
ifndef READTHEDOCS
	$(BROWSER) docs/_build/html/index.html
endif

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/xclim*.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ --private --module-first xclim xclim/testing/tests
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
ifndef READTHEDOCS
	$(BROWSER) docs/_build/html/index.html
endif

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python -m pip install --no-user .

develop: clean ## install the package and development dependencies in editable mode to the active Python's site-packages
	python -m pip install --no-user --editable ".[dev]"

upstream: clean develop ## install the GitHub-based development branches of dependencies in editable mode to the active Python's site-packages
	python -m pip install --no-user --requirement requirements_upstream.txt
