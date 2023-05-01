# New web2 user

## Request

This API makes a request to create a new user with the provided display name and credentials

### Endpoint

The request can be made to the endpoint `/{stage}/users/web2/new` where `stage` is one of the following

- `dev`: used for testing/expiramental features. Do **not** use for production applications
- `prod`: used to provide a stable version. **NEW**
    

### Payload

The payload for this request requires a JSON document consisting of a single key: `NewAccount`. The value is a base 64 encoded string representing the `credentials` of the new web2 user. When decoded the credentials for follow the format `user:pass`. Sample structure as follows

``` json
{
    "NewAccount": "<Base 64 encoded credentials>"
}

```

## Responses

There are two possible responses.

### Valid

This response indicate the new user was successfully created. Its status code will be `201`

``` json
{
    "success": {
        "message": "CREATED NEW USER"
    }
}

```

### Errors

There are to possible error states that can arise

#### Bad request

This indicates that the request could not be processed. Its status code will be `400`. Consult the payload section are verify everything is formatted correctly then try again.

``` json
{
    "error": {
        "message": "The error reason"
    }
}

```

#### Bad gateway

This indicates that the request failed because dependent service failed. Its status code will be `503`. This may be due to throttling or a timeout. Most of these should resolve themselves after a brief backoff and then trying again.

``` json
{
    "error": {
        "message": "The error reason"
    }
}

```

#### Internal server error

This indicates that the request failed due to an unforeseen circumstance. If you receive one of these (status code `502`), and are able to reliably reproduce it, open a new issue [here](https://github.com/idea-bank/services/issues) and tagged it with `create-user-web2` label. Include any relevant details and let the service team know.
