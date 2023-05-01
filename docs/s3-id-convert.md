# S3 identifier conversion

## Request

This API makes a request to generate a share link to the specified resource in a specified bucket

### Endpoint

The request can be made to the endpoint `GET /{stage}/blobs` where `stage` is one of the following

- `dev`: used for testing/expiramental features. Do **not** use for production applications
- `prod`: used to provide a stable version. **COMING SOON**
    

### Query parameters

This endpoint expects two query parameters. If one or more are missing, an error response will be returned. Extraneous query parameters are ignored.

- bucket: the bucket that holds the resource you are requesting
- key: the name of the object that you are requesting

Given these parameters, a full request might look like the following

```
GET /{stage}/blobs?bucket=bucket-name&key=object-name
```

**Make sure to URL encode your query string**

## Responses

There are three possible responses: Ok, bad request, gateway timeout

### Valid

This response indicate a new share link was successfully generated. It is valid for 5 minutes.

``` json
{
    "success": {
        "link": "<share link>"
    }
}

```

### Errors

There are two possible error states that can arise. If you request is missing query parameters, the response will be `400`. If there was a timeout, the response will be `504` and you should try again after a short while.

#### Bad request

``` json
{
    "error": {
        "message": "Message indicating which parameter was missing"
    }
}

```

#### Gateway timeout

```json
{
    "error": {
        "message": "Message indicating a timeout"
    }
}
```

#### Internal server error

This indicates that the request failed due to an unforeseen circumstance. If you receive one of these (status code `502`), and are able to reliably reproduce it, open a new issue [here](https://github.com/idea-bank/services/issues) and tagged it with `s3-id-convert` label. Include any relevant details and let the service team know.
