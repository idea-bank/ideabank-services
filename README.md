# ideabank-webapi

## About

An API for the services utilized by the Idea Bank application. This is a REST API written in Python using the [FastAPI](https://fastapi.tiangolo.com) framework. Supported version of python are: 3.8, 3.9, 3.10, 3.11.

## Getting started

### Development enviroment

This project utilizes a python virtual environment to set up the development environment. A `Makefile` is included to speed up the process. Simply run the following to get started

```shell
$ make bootstrap
$ source .venv/bin/activate
```

Once set up, there are a few extra tools to help out during development. You can run `make test` to run the suite of unit tests using [pytest](https://docs.pytest.org/en/7.3.x/) included in the `test/` directory. You can also run `make lint` to perform lint checks using [pylint](https://pylint.readthedocs.io/en/stable/).

When you all done, or you need a fresh slate, run `make clean` to clean up all build artifacts and the virtual environment.

Each make target is divided up into smaller targets. For a list of all target, run `make help` or `make`.

### Deployment

The recommended deployment method is with a container image. A docker file is provided to build an image to run this API from. To build the image run the following

```shell
$ docker build . -t webapi
```

Once built, the image can be deployed wherever you'd like. For example, to deploy this locally, you can run the following

```shell
$ docker run --env-file .env -d -p 8000:80 --rm --name testapi webapi
```

With deployment, you'll need to include the following environment variables

```
DBHOST=<your-db-host>
DBPORT=<your-db-port>
DBUSER=<your-db-user>
DBPASS=<your-db-password>
DBNAME=<your-db-name>
S3HOST=<your-aws-url>
S3KEY=<your-aws-key>
S3SECRET=<your-aws-secret>
S3NAME=<your-bucket-name>
JWT_SIGNER=<your-signing-key>
JWT_HASHER=<your-signing-algorithm>
```

For setting up a mock data environment, see the [here](./data/README.md) to get started.

## Contributors

- Nathan Mendoza (nathancm@uci.edu)
