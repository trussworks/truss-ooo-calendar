run:
	./main.py

test:
	mypy *.py
	python3 -m unittest discover

.PHONY: run test
