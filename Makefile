.PHONY: lint

lint: masha/*.py
	python3 -m black masha/*.py