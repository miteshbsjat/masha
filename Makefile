.PHONY: lint test clean

py_src_files = masha/*.py masha/filters/*.py masha/tests/*.py

lint: $(py_src_files)
	python3 -m black $(py_src_files)
	autoflake --in-place --remove-unused-variables $(py_src_files)
	ruff check $(py_src_files)
	pylint $(py_src_files)

test: masha/*.py test/test_*.py
	python3 -m unittest test/test_*.py

clean:
	find . -name "__pycache__" | xargs -L 1 rm -rvf
