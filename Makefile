.PHONY: lint

lint: masha/*.py
	python3 -m black masha/*.py
	autoflake --in-place --remove-unused-variables masha/*.py
	ruff check masha/
	pylint masha/*.py