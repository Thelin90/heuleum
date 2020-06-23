include .env

build: clean deps

.PHONY: clean
clean:
	-find . -type f -name "*.pyc" -delete
	-find . -type f -name "*.cover" -delete

.PHONY: deps
deps:
	pipenv sync --dev --python 3.7

.PHONY: update
update:
	pipenv update --dev --python 3.7

.PHONY: pythonpath
pythonpath:
	 echo "PYTHONPATH=${PWD}/src/" >> .env

.PHONY: pre_commit_py37
pre_commit_py37:
	pipenv run pre-commit

.PHONY: test-ipdb
test-ipdb:
	pipenv run python -m pytest $(pytest_test_args) --cov-config=.coveragerc --cov=src tests/$(pytest_test_type) -s

.PHONY: test
test:
	pipenv run python -m pytest $(pytest_test_args) --cov-config=.coveragerc --cov=src tests/$(pytest_test_type)

.PHONY: tear-heuleum-up
tear-heuleum-up:
	docker-compose -f tools/docker/docker-compose-local.yaml up $(heuleum_tear_up_args)

.PHONY: tear-heuleum-down
tear-heuleum-down:
	docker-compose -f tools/docker/docker-compose-local.yaml down

.PHONY: create_topics
create_topics:
	pipenv run python src/utils/local/publish.py event-tracker create events
	pipenv run python src/utils/local/publish.py event-tracker-deadletter create deadletter_events

.PHONY: list_topics
list_topics:
	pipenv run python src/utils/local/publish.py event-tracker list
	pipenv run python src/utils/local/publish.py event-tracker-deadletter list
