.PHONY: lint test clean

py_src_files = masha/*.py masha/filters/*.py masha/tests/*.py

py_test_files = test/test_*.py

lint: $(py_src_files)
	python3 -m black $^
	autoflake --in-place --remove-unused-variables $^
	isort masha/
	ruff check $^
	pylint $^
	black $^

test: $(py_src_files) $(py_test_files)
	python3 -m unittest $(py_test_files)

clean:
	find . -name "__pycache__" | xargs -L 1 rm -rvf
