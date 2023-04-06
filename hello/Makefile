# Makefile for ideabank hello service
#
SERVICE_NAME=hello
SOURCES=function.py
DEPS=.venv/lib/python3.9/site-packages/*
SERVICE_TESTER=test_function.py
BRANCH=$(shell git branch --show-current)
AWS_PROD=$(AWS_SERVICE_PROD)
AWS_DEV=$(AWS_SERVICE_DEV)

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

clean-cov: ## Remove coverage artifacts
	find . -name .coverage -exec rm -f {} +

clean: clean-pyc clean-venv clean-zip clean-cov ## Clean up develepment environment

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
		coverage run $(SERVICE_TESTER); \
		coverage report -m; \
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
	@( \
		if [ $(BRANCH) == "main" ]; then \
			aws lambda list-functions --profile=$(AWS_PROD) | grep $(SERVICE_NAME)-prod; \
			if [ $? -eq 0 ]; then \
				aws lambda update-function-code \
					--function-name $(SERVICE_NAME)-prod \
					--zip-file fileb://$(SERVICE_NAME).zip \
					--profile=$(AWS_PROD); \
			else \
				aws lambda create-function \
					--function-name=$(SERVICE_NAME)-prod \
					--handler=function.handler \
					--zip-file fileb://$(SERVICE_NAME).zip \
					--role=arn:aws:iam::272377214389:role/SimpleService \
					--runtime=python3.9 \
					--environment=Variables={"ENV"="prod"} \
					--profile=$(AWS_PROD); \
			fi \
		elif [ $(BRANCH) == "dev" ]; then \
			aws lambda list-functions --profile=$(AWS_DEV) | grep $(SERVICE_NAME)-dev; \
			if [ $? -eq 0 ]; then \
				aws lambda update-function-code \
					--function-name $(SERVICE_NAME)-dev \
					--zip-file fileb://$(SERVICE_NAME).zip \
					--profile=$(AWS_DEV); \
			else \
				aws lambda create-function \
					--function-name=$(SERVICE_NAME)-dev \
					--handler=function.handler \
					--zip-file fileb://$(SERVICE_NAME).zip \
					--role=arn:aws:iam::563842661877:role/SimpleService \
					--runtime=python3.9 \
					--environment=Variables={"ENV"="dev"} \
					--profile=$(AWS_DEV); \
			fi \
		else \
			echo Not deploying, can only deploy on main or dev branches; \
			exit 1; \
		fi \
	)
