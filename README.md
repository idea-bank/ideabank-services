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

1) Run the new-service.sh script
2) Provide the name of the service when prompted

```
	$ ./new-service.sh
	Service Name: <Enter service name here
```

The service will not be deployable until backend infrastructure is allocated for it. Afterward, the service can continually be deployed using the provided Makefile

## The services

### Hello

A simple microservice that echoes back the event and context information as JSON.
