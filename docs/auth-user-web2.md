# Auth web2 user

## Request

This API makes a request to authenticate a user with the provided credentials or verify a previously issued token

### Endpoint

The request can be made to the endpoint `POST /{stage}/users/web2/auth` where `stage` is one of the following

- `dev`: used for testing/expiramental features. Do **not** use for production applications
- `prod`: used to provide a stable version. **COMING SOON**
    

### Payload

The payload of this request has two forms. The first is for the first time authenticating with a provided username and password. The second is for verifying the validity of a previously issued access token. In both cases, a key in the payload will indicated which branch of the service will run. The `AuthKeyType` key can take on the following values:

- `Username+Password`
- `WebToken`

Any other value is considered invalide and will return an error. If the `Username+Password` value is specifed the payload will take the following form

``` json
{
    "AuthKeyType": "Username+Password",
    "Credentials": {
        "username": "<username claiming ownership of the provided auth token>",
        "jwt": "<Token>"
    }
}
```


## Responses

There are two possible responses. Ok, or unauthorized

### Valid

This response indicate the new user was successfully created. Its status code will be `200` If the `AuthKeyType` was `Username+Password` a new auth token is included for future use.

``` json
{
    "success": {
        "jwt": "<new auth token (included only on first time authentication)>"
        "message": "Authenticated"
    }
}

```

### Errors

There are to possible error states that can arise. In any case, the response will be unauthorized(`401`). Messages will be purposefully vague as an additional security measure. Consult service logs to identify issues.


``` json
{
    "error": {
        "message": "A purposefully vague error message"
    }
}

```

#### Internal server error

This indicates that the request failed due to an unforeseen circumstance. If you receive one of these (status code `502`), and are able to reliably reproduce it, open a new issue [here](https://github.com/idea-bank/services/issues) and tagged it with `auth-user-web2` label. Include any relevant details and let the service team know.
