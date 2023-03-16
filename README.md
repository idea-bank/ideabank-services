# Services

## Getting started

### Environment

Each service has the following files

- Dockerfile: allows local testing in a docker container
- Makefile: collection of rules to speed up testing/linting and deployment
- function.py: the primary file for the service code. All code for a service should go here. If its getting too big, consider breaking it up into multiple services
- test_function.py: file to testing service logic. It will not be included when the service is deployed
- requirements.txt: file to list the services' external dependencies

### New services

1) Use [this](https://github.com/idea-bank/aws-lambda-basic-handler) [cookiecutter](https://github.com/cookiecutter/cookiecutter) to generate the project
2) Follow the prompts to complete the process

```bash
$ cookiecutter https://github.com/idea-bank/aws-lambda-basic-handler
service_name [A name for your service]: <a-name-for-your-service>
service_author [Your Name]: <enter your name>
service_execution_policy [...]: <execution ARN>
service_description [Describe your new service]: <description for your service>
```

The service will not be deployable until backend infrastructure is allocated for it. Afterward, the service can continually be deployed using the provided Makefile

## The services

### `hello`

A simple microservice that echoes back the event and context information as JSON.

### `create-user-web2`

A microservice that creates ideabank users through traditional web2 conventions
