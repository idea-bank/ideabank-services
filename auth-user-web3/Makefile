# Makefile for ideabank auth-user-web3 service

SERVICE_NAME=auth-user-web3
SERVICE_HANDLER=function.py
SERVICE_TESTER=test_function.py
SERVICE_CREDS=?

help:
	@echo "Makefile for ideabank $(SERVICE_NAME) service. Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

venv: ## Setup a virtual environment
	[ -d .venv ] || python3 -m venv .venv --prompt=ideabank-$(SERVICE_NAME)

clean-venv: ## Destroy the virtual environment if it exists
	[ ! -d .venv ] || rm -rf .venv

clean-pyc: ## Remove package artifacts and cached byte code
	find . -name __pycache__ -exec rm -rf {} +

clean-zip: ## Remove package zip archive
	find . -name $(SERVICE_NAME).zip -exec rm -f {} +

clean: clean-venv clean-zip ## Clean up develepment environment

activate: ## Activate the virtual environment for bootstrapping (does NOT activate for you).
	@echo 
	@echo
	@echo "Virtual environment created!"
	@echo "Activate it by running the following:"
	@echo
	@echo "    source .venv/bin/activate"
	@echo 

.PHONY: test
test: ## Run unittests on the source directory
	@python3 $(SERVICE_TESTER)

.PHONY: lint
lint: ## Run lint checks on the source directory
	pylint $(SERVICE_HANDLER)

zip: bootstrap
	zip $(SERVICE_NAME).zip $(SERVICE_HANDLER)

bootstrap: venv ## Bootstrap the virtual environment
	@( \
		source .venv/bin/activate; \
		pip3 install --upgrade pip; \
		pip3 install --require-virtualenv -r requirements.txt; \
	)
	@$(MAKE) activate

docker: lint test ## Test the microservice in a local docker environment
	docker build -t $(SERVICE_NAME) .
	docker run -p 9000:8080 $(SERVICE_NAME)

deploy: lint test zip ## Deploy the microservice to AWS lambda
	aws lambda update-function-code --function-name $(SERVICE_NAME) --zip-file fileb://$(SERVICE_NAME).zip --profile=$(SERVICE_CREDS)
