.PHONY: lint

lint: masha/*.py
	python3 -m black masha/*.py
	autoflake --in-place --remove-unused-variables masha/*.py
	pylint masha/*.py