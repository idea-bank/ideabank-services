# ideabank-webapi mock data

## About

A collection of tools designed to mock a significant amount of data that can be used to test and develop the API. The tools include a database schema creation script to load up the expected schema into a database. It also includes a way to mock and AWS S3 compatible storage server locally. 

## Setup

### Generate the data

To generate a set of mock data simply run the `dummy_data.py`. This should be done within the virtual environment created when bootstrapping the development environment. This can take a few minutes.

```shell
$ python dummy_data.py
```

The following data will be generated:

- Database rows corresponding the the schema in `create_schema.sql`. Each table in its own csv file
- Random colored square images representing image media files available to the API

### Starting the test database

After running the the data generation script, use the following command to get a local test database with a nontrivial amount of data to play around with

```shell
$ docker build . -t testdb
$ docker run --name devdb --rm -d -p 8888:5432 testdb
```

**If you'd like the test database to persist between restarts, withhold the `--rm` flag from the run command**

### Starting the mock s3 server

After running the data generation script, use the following command to get a local s3 server with a nontrivial number of files to play around with

```shell
$ docker run -d -p 9090:9090 -p 9191:9191 -e initialBuckets=test -e debug=true --rm --name s3mock -t adobe/s3mock
```

This will start the s3 mock server with a singular `test` bucket. It also provides two access points. One for HTTP (9090) and one for HTTPS (9191). However, the bucket is empty and needs some files placed into it. That can be done with the following

```shell
$ aws s3 cp thumbnails/ s3://test/thumbnails --recursive --endpoint-url=http://localhost:9090
$ aws s3 cp avatars/ s3://test/avatars --recursive --endpoint-url=http://localhost:9090
```

This will load up the test bucket with quite a few files, so it may take a while. It is **highly recommended** to use the aws cli to do this part, or you'll spend quite a bit of time setting this up yourself.

**If you'd like the test s3 bucket to persist between restarts, withhold the `--rm` flag from the run command**

## Contributors

- Nathan Mendoza (nathancm@uci.edu)
