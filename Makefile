.PHONY: lint test

lint: masha/*.py
	python3 -m black masha/*.py
	autoflake --in-place --remove-unused-variables masha/*.py
	ruff check masha/
	pylint masha/*.py

test: masha/*.py test/test_*.py
	python3 -m unittest test/test_*.py
