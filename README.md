# Python Client Abstraction
I have often found that I am constantly writing similar clients to
in order to provide an abstraction around a third party API.

This client abstraction aims to reduce the overhead of writing the client,
and should allow the consumer of the APIs to focus on the high level
implementation, rather than the design of the client itself.

## Installation

```
pip install api-client
```

## Usage

```
from apiclient import BaseClient
from apiclient.decorates import endpoint


# Define endpoints, using the provided decorator.
@endpoint(base_url="https://jsonplaceholder.typicode.com")
class Endpoint:
    todos = "todos"
    todo = "todos/{id}"


# Extend the client for your API integration.
class JSONPlaceholderClient(BaseClient):

    def get_all_todos(self) -> dict:
        return self.read(Endpoint.todos)

    def get_todo(self, todo_id: int) -> dict:
        url = Endpoint.todo.format(id=todo_id)
        return self.read(url)


# Initialize the client with the correct authentication method,
# response handler and request formatter.
>>> client = JSONPlaceholderClient(
    authentication_method=HeaderAuthentication(token="<secret_value>"),
    response_handler=JsonResponseHandler,
    request_formatter=JsonRequestFormatter,
)


# Call the client methods.
>>> client.get_all_todos()
[
    {
        'userId': 1,
        'id': 1,
        'title': 'delectus aut autem',
        'completed': False
    },
    ...,
    {
        'userId': 10,
        'id': 200,
        'title': 'ipsam aperiam voluptates qui',
        'completed': False
    }
]


>>> client.get_todo(45)
{
    'userId': 3,
    'id': 45,
    'title': 'velit soluta adipisci molestias reiciendis harum',
    'completed': False
}


# REST APIs correctly adhering to the status codes to provide meaningful
# responses will raise the appropriate exeptions.
>>> client.get_todo(450)
ClientBadRequestError: 404 Error: Not Found for url: https://jsonplaceholder.typicode.com/todos/450

>>> try:
...     client.get_todo(450)
... except ClientError:
...     print("All client exceptions inherit from ClientError")
"All client exceptions inherit from ClientError"

```

## Authentication Methods
Authentication methods provide a way in which you can customize the
client with various authentication schemes through dependency injection,
meaning you can change the behaviour of the client without changing the
underlying implementation.

The apiclient supports the following authentication methods, by specifying
the initialized class on initialization of the client, as follows:
```
client = ClientImplementation(
   authentication_method=<AuthenticationMethodClass>(),
   response_handler=...,
   request_formatter=...,
)
```

### `NoAuthentication`
This authentication method simply does not add anything to the client,
allowing the api to contact APIs that do not enforce any authentication.

### `QueryParameterAuthentication`
This authentication method adds the relevant parameter and token to the
client query parameters.  Usage is as follows:

```
authentication_method=QueryParameterAuthentication(parameter="apikey", token="secret_token"),
```
Example. Contacting a url with the following data
```
http://api.example.com/users?age=27
```
Will add the authentication parameters to the outgoing request:
```
http://api.example.com/users?age=27&apikey=secret_token
```

### `HeaderAuthentication`
This authentication method adds the relevant authorization header to
the outgoing request.  Usage is as follows:
```
authentication_method=HeaderAuthentication(token="secret_value")

# Constructs request header:
{"Authorization": "Bearer secret_value"}
```
The `Authorization` parameter and `Bearer` realm can be adjusted by
specifying on method initialization.
```
authentication_method=HeaderAuthentication(
   token="secret_value"
   parameter="Foo",
   realm="Bar",
)

# Constructs request header:
{"Foo": "Bar secret_value"}
```

Or alternatively, when APIs do not require a realm to be set, you can
specify it as a value that evaluates to False to remove the realm from
the header:
```
authentication_method=HeaderAuthentication(
   token="secret_value"
   parameter="Foo",
   realm=None,
)

# Constructs request header:
{"Foo": "secret_value"}
```

### `BasicAuthentication`
This authentication method enables specifying a username and password to APIs
that require such.
```
authentication_method=BasicAuthentication(username="foo", password="secret_value")
```

## Response Handlers

Response handlers provide a standard way of handling the final response
following a successful request to the API.  These must inherit from
`BaseResponseHandler` and implement the `get_request_data()` method which
will take the `requests.Response` object and parse the data accordingly.

The apiclient supports the following response handlers, by specifying
the class on initialization of the client as follows:

```
client = ClientImplementation(
   authentication_method=...,
   response_handler=<ResponseHandlerClass>,
   request_formatter=...,
)
```

### `RequestsResponseHandler`
Handler that simply returns the original `Response` object with no
alteration.

### `JsonResponseHandler`
Handler that parses the response data to `json` and returns the dictionary.
If an error occurs trying to parse to json then a `ClientUnexpectedError`
will be raised.

### `XmlResponseHandler`
Handler that parses the response data to an `xml.etree.ElementTree.Element`.
If an error occurs trying to parse to xml then a `ClientUnexpectedError`
will be raised.

## Request Formatters

Request formatters provide a way in which the outgoing request data can
be encoded before being sent, and to set the headers appropriately.

These must inherit from `BaseRequestFormatter` and implement the `format()`
method which will take the outgoing `data` object and format accordingly
before making the request.

The apiclient supports the following request formatters, by specifying
the class on initialization of the client as follows:

```
client = ClientImplementation(
   authentication_method=...,
   response_handler=...,
   request_formatter=<RequestFormatterClass>,
)
```

### `JsonRequestFormatter`

Formatter that converts the data into a json format and adds the
`application/json` Content-type header to the outoing requests.


## Exceptions

All exceptions raised as part of the apiclient inherit from `ClientError`.

### `ClientBadRequestError`
The client was used incorrectly for contacting the API. This is due
primarily to user input by passing invalid data to the API.

### `ClientRedirectionError`
A redirection status code was returned as a final code when making the
request. This means that no data can be returned to the client as we could
not find the requested resource as it had moved.

### `ClientServerError`
The API was unreachable when making the request.

### `ClientUnexpectedError`
An unexpected error occurred when using the client.  This will most likely
be the result of another exception being raised.  If possible, the original
exception will be indicated as the causing exception of this error.


## Endpoints

The apiclient also provides a convenient way of defining url endpoints with
use of the `@endpoint` decorator.  In order to decorate a class with `@endpoint`
the decorated class must define a `base_url` attribute along with the required
resources.  The decorator will combine the base_url with the resource.

Example:

```
from apiclient.decorates import endpoint

@endpoint(base_url="http://foo.com")
class Endpoint:
    resource = "search"

>>> Endpoint.resource
"http://foo.com/search
```