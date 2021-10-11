SHELL = /bin/bash
PRE-COMMIT := $(shell which pre-commit)

run:
	./main.py

test: .prereqs.stamp
	mypy *.py
	python3 -m unittest discover

# Shortcut to run pre-commit hooks over the entire repo.
pre-commit: .git/hooks/pre-commit
	pre-commit run --all-files

# Update the pre-commit hooks if the pre-commit binary is updated.
.git/hooks/pre-commit: $(PRE-COMMIT)
	pre-commit install

.prereqs.stamp: prereqs.conf
	bin/prereqs -c prereqs.conf
	touch .prereqs.stamp

clean:
	rm -f .*.stamp

.PHONY: run test clean pre-commit
