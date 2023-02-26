#! /bin/bash

LAST_INPUT=

function prompt_for() {
	echo -n $1
	read LAST_INPUT
}

function create_service_env() {
	mkdir ${LAST_INPUT}
	if [ $? -ne 0 ]
	then
		echo Could not create service ${LAST_INPUT}. It may already exist
		exit 1
	fi
	for file in "Makefile" "Dockerfile" "function.py" "test_function.py" "requirements.txt" 
	do
		touch ${LAST_INPUT}/${file}
	done
}

function gen_docker_file() {
	echo "FROM public.ecr.aws/lambda/python:3.9" >> ${LAST_INPUT}/Dockerfile
	echo "" >> ${LAST_INPUT}/Dockerfile
	echo "COPY requirements.txt ." >> ${LAST_INPUT}/Dockerfile
	echo 'RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"' >> ${LAST_INPUT}/Dockerfile
	echo "" >> ${LAST_INPUT}/Dockerfile
	echo 'COPY function.py "${LAMBDA_TASK_ROOT}"' >> ${LAST_INPUT}/Dockerfile
	echo "" >> ${LAST_INPUT}/Dockerfile
	echo 'CMD [ "function.handler" ]' >> ${LAST_INPUT}/Dockerfile

}

function gen_handler_file() {
	echo '"""' >> ${LAST_INPUT}/function.py
    	echo '    :module_name: function' >> ${LAST_INPUT}/function.py
    	echo '    :module_summary: #TODO' >> ${LAST_INPUT}/function.py
    	echo '    :module_author: #TODO' >> ${LAST_INPUT}/function.py
	echo '"""' >> ${LAST_INPUT}/function.py
	echo '' >> ${LAST_INPUT}/function.py
	echo 'import sys' >> ${LAST_INPUT}/function.py
	echo '' >> ${LAST_INPUT}/function.py
	echo 'def handler(event, context):' >> ${LAST_INPUT}/function.py
    	echo '    """A function that returns a simple greeting response"""' >> ${LAST_INPUT}/function.py
    	echo '    return {' >> ${LAST_INPUT}/function.py
        echo '        "sysinfo": sys.version,' >> ${LAST_INPUT}/function.py 
        echo '        "event": event,' >> ${LAST_INPUT}/function.py
        echo '        "context": str(context)' >> ${LAST_INPUT}/function.py
        echo '    }' >> ${LAST_INPUT}/function.py

}

function gen_test_handler_file() {
	echo '"""' >> ${LAST_INPUT}/test_function.py
	echo '    :module_name: test_function' >> ${LAST_INPUT}/test_function.py
	echo '    :module_summary: #TODO' >> ${LAST_INPUT}/test_function.py
	echo '    :module_author: #TODO' >> ${LAST_INPUT}/test_function.py
	echo '"""' >> ${LAST_INPUT}/test_function.py
	echo '' >> ${LAST_INPUT}/test_function.py
	echo 'import unittest' >> ${LAST_INPUT}/test_function.py
	echo '' >> ${LAST_INPUT}/test_function.py
	echo "if __name__ == '__main__':" >> ${LAST_INPUT}/test_function.py
	echo '    unittest.main()' >> ${LAST_INPUT}/test_function.py
}

function gen_make_file() {
	echo '# Makefile for ideabank' ${LAST_INPUT} 'service' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'SERVICE_NAME='${LAST_INPUT} >> ${LAST_INPUT}/Makefile
	echo 'SERVICE_HANDLER=function.py' >> ${LAST_INPUT}/Makefile
	echo 'SERVICE_TESTER=test_function.py' >> ${LAST_INPUT}/Makefile
    echo 'SERVICE_CREDS=$(AWS_SERVICE)' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'help:' >> ${LAST_INPUT}/Makefile
	echo '	@echo "Makefile for ideabank $(SERVICE_NAME) service. Available targets:"' >> ${LAST_INPUT}/Makefile
	echo "	@grep -E ""'^[a-zA-Z_-]+:.*?## .*\$\$' ""$""(MAKEFILE_LIST) | sort | awk" "'BEGIN {FS = \":.*?## \"}; {printf \"\033[36m%-30s\033[0m %s\n\", \$\$1, \$\$2}'" >> ${LAST_INPUT}/Makefile
	echo >> ${LAST_INPUT}/Makefile
	echo 'venv: ## Setup a virtual environment' >> ${LAST_INPUT}/Makefile
	echo '	[ -d .venv ] || python3 -m venv .venv --prompt=ideabank-$(SERVICE_NAME)' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'clean-venv: ## Destroy the virtual environment if it exists' >> ${LAST_INPUT}/Makefile
	echo '	[ ! -d .venv ] || rm -rf .venv' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'clean-pyc: ## Remove package artifacts and cached byte code' >> ${LAST_INPUT}/Makefile
	echo '	find . -name __pycache__ -exec rm -rf {} +' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'clean-zip: ## Remove package zip archive' >> ${LAST_INPUT}/Makefile
	echo '	find . -name $(SERVICE_NAME).zip -exec rm -f {} +' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'clean: clean-venv clean-zip ## Clean up develepment environment' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'activate: ## Activate the virtual environment for bootstrapping (does NOT activate for you).'>> ${LAST_INPUT}/Makefile 
	echo '	@echo ' >> ${LAST_INPUT}/Makefile
	echo '	@echo' >> ${LAST_INPUT}/Makefile
	echo '	@echo "Virtual environment created!"' >> ${LAST_INPUT}/Makefile
	echo '	@echo "Activate it by running the following:"' >> ${LAST_INPUT}/Makefile
	echo '	@echo' >> ${LAST_INPUT}/Makefile
	echo '	@echo "    source .venv/bin/activate"' >> ${LAST_INPUT}/Makefile
	echo '	@echo ' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo '.PHONY: test' >> ${LAST_INPUT}/Makefile
	echo 'test: ## Run unittests on the source directory' >> ${LAST_INPUT}/Makefile
	echo '	@python3 $(SERVICE_TESTER)' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo '.PHONY: lint' >> ${LAST_INPUT}/Makefile
	echo 'lint: ## Run lint checks on the source directory' >> ${LAST_INPUT}/Makefile
	echo '	pylint $(SERVICE_HANDLER)' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'zip: bootstrap' >> ${LAST_INPUT}/Makefile
	echo '	zip $(SERVICE_NAME).zip $(SERVICE_HANDLER)' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'bootstrap: venv ## Bootstrap the virtual environment' >> ${LAST_INPUT}/Makefile
	echo '	@( \' >> ${LAST_INPUT}/Makefile
	echo '		source .venv/bin/activate; \' >> ${LAST_INPUT}/Makefile
	echo '		pip3 install --upgrade pip; \' >> ${LAST_INPUT}/Makefile
	echo '		pip3 install --require-virtualenv -r requirements.txt; \' >> ${LAST_INPUT}/Makefile
	echo '	)' >> ${LAST_INPUT}/Makefile
	echo '	@$(MAKE) activate' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'docker: lint test ## Test the microservice in a local docker environment' >> ${LAST_INPUT}/Makefile
	echo '	docker build -t $(SERVICE_NAME) .' >> ${LAST_INPUT}/Makefile
	echo '	docker run -p 9000:8080 $(SERVICE_NAME)' >> ${LAST_INPUT}/Makefile
	echo '' >> ${LAST_INPUT}/Makefile
	echo 'deploy: lint test zip ## Deploy the microservice to AWS lambda' >> ${LAST_INPUT}/Makefile
	echo '	aws lambda update-function-code --function-name $(SERVICE_NAME) --zip-file fileb://$(SERVICE_NAME).zip --profile=$(SERVICE_CREDS)' >> ${LAST_INPUT}/Makefile
}

function main() {
	prompt_for "Service Name: "
	create_service_env
	gen_docker_file
	gen_handler_file
	gen_test_handler_file
	gen_make_file
}

main
