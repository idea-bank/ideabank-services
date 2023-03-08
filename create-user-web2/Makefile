# Makefile for ideabank create-user-web2 service
#
SERVICE_NAME=create-user-web2
SOURCES=function.py
DEPS=.venv/lib/python3.9/site-packages/*
SERVICE_TESTER=test_function.py
SERVICE_CREDS=$(AWS_SERVICE)

help:
	@echo "Makefile for ideabank $(SERVICE_NAME) service. Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

venv: ## Setup a virtual environment
	[ -d .venv ] || python3.9 -m venv .venv --prompt=ideabank-$(SERVICE_NAME)

clean-venv: ## Destroy the virtual environment if it exists
	[ ! -d .venv ] || rm -rf .venv

clean-pyc: ## Remove package artifacts and cached byte code
	find . -name __pycache__ -exec rm -rf {} +

clean-zip: ## Remove package zip archive
	find . -name $(SERVICE_NAME).zip -exec rm -f {} +

clean: clean-pyc clean-venv clean-zip ## Clean up develepment environment

activate: ## Activate the virtual environment for bootstrapping (does NOT activate for you).
	@echo 
	@echo
	@echo "Virtual environment created!"
	@echo "Activate it by running the following:"
	@echo
	@echo "    source .venv/bin/activate"
	@echo 

.PHONY: test
test: bootstrap ## Run unittests on the source directory
	@( \
		source .venv/bin/activate; \
		python3 $(SERVICE_TESTER); \
	)

.PHONY: lint
lint: bootstrap ## Run lint checks on the source directory
	@( \
		source .venv/bin/activate; \
		pylint $(SOURCES); \
	)

zip: test lint
	zip $(SERVICE_NAME).zip $(SOURCES) $(DEPS)

bootstrap: venv ## Bootstrap the virtual environment
	@( \
		source .venv/bin/activate; \
		pip3 install --upgrade pip; \
		pip3 install --require-virtualenv -r requirements.txt; \
		pip3 install --require-virtualenv -r dev_requirements.txt; \
	)
	@$(MAKE) activate

docker: lint test ## Test the microservice in a local docker environment
	docker build -t $(SERVICE_NAME) .
	docker run -p 9000:8080 $(SERVICE_NAME)

deploy: zip ## Deploy the microservice to AWS lambda
ifeq ($(shell git branch --show-current), main)
	aws lambda update-function-code --function-name $(SERVICE_NAME) --zip-file fileb://$(SERVICE_NAME).zip --profile=$(SERVICE_CREDS)
else
	$(error Not deploying. Expected banch to be `main`, was $(shell git branch --show-current) instead)
endif
