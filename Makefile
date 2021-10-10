run:
	./main.py

test:
	python3 -m unittest discover
	mypy *.py

.PHONY: run test
