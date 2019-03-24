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
from apiclient.paginators import paginated
from apiclient.retrying import retry_request



# Define endpoints, using the provided decorator.
@endpoint(base_url="https://jsonplaceholder.typicode.com")
class Endpoint:
    todos = "todos"
    todo = "todos/{id}"


def get_next_page(response):
    return {
        "limit": response["limit"],
        "offset": response["offset"] + response["limit"],
    }


# Extend the client for your API integration.
class JSONPlaceholderClient(BaseClient):

    @paginated(by_query_params=get_next_page)
    def get_all_todos(self) -> dict:
        return self.read(Endpoint.todos)

    @retry_request
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
NotFound: 404 Error: Not Found for url: https://jsonplaceholder.typicode.com/todos/450

>>> try:
...     client.get_todo(450)
... except APIClientError:
...     print("All client exceptions inherit from APIClientError")
"All client exceptions inherit from APIClientError"

```

## BaseClient Interface
The `BaseClient` provides the following public interface:
* `create(self, endpoint: str, data: dict, params: OptionalDict = None)`

   Delegate to POST method to send data and return response from endpoint.

* `read(endpoint: str, params: OptionalDict = None)`

   Delegate to GET method to get response from endpoint.

* `replace(endpoint: str, data: dict, params: OptionalDict = None)`

   Delegate to PUT method to send and overwrite data and return response from endpoint.

* `update(endpoint: str, data: dict, params: OptionalDict = None)`

   Delegate to PATCH method to send and update data and return response from endpoint

* `delete(endpoint: str, params: OptionalDict = None)`

   Delegate to DELETE method to remove resource located at endpoint.

* `get_request_timeout() -> float`

   By default, all requests have been set to have a default timeout of 10.0 s.  This
   is to avoid the request waiting forever for a response, and is recommended
   to always be set to a value in production applications.  It is however possible to
   override this method to return the timeout required by your application.


## Retrying

To add some robustness to your client, the power of [tenacity](https://github.com/jd/tenacity)
has been harnessed to add a `@retry_request` decorator to the `apiclient` toolkit.

This will retry any request which responds with a 5xx status_code (which is normally safe
to do as this indicates something went wrong when trying to make the request), or when an
`UnexpectedError` occurs when attempting to establish the connection.

`@retry_request` has been configured to retry for a maximum of 5 minutes, with an exponential
backoff strategy.  For more complicated uses, the user can use tenacity themselves to create
their own custom decorator.

Usage:

```
from apiclient.retrying import retry_request

class MyClient(BaseClient):

    @retry_request
    def retry_enabled_method():
        ...

```

## Pagination

In order to support contacting pages that respond with multiple pages of data when making read requests,
add a `@paginated` decorator to your client method.  `@paginated` can paginate the requests either where
the pages are specified in the query parameters, or by modifying the url.

Usage is simple in both cases; write a function that takes the response data and return the next page
to fetch.  If the response is the last page, the function should return None or raise an error.

Usage:

```
from apiclient.paginators import paginated


def next_page_by_params(response):
    # Function reads the response data and returns the query param
    # that tells the next request to go to.
    return {"next": response["pages"]["next"]


def next_page_by_url(response):
    # Function reads the response and returns the url as string
    # where the next page of data lives.
    return response["pages"]["next"]["url"]


class MyClient(BaseClient):

    @paginated(by_query_params=next_page_by_params)
    def paginated_example_one():
        ...

    @paginated(by_url=next_page_by_url)
    def paginated_example_two():
        ...

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
The `Authorization` parameter and `Bearer` scheme can be adjusted by
specifying on method initialization.
```
authentication_method=HeaderAuthentication(
   token="secret_value"
   parameter="Foo",
   scheme="Bar",
)

# Constructs request header:
{"Foo": "Bar secret_value"}
```

Or alternatively, when APIs do not require a scheme to be set, you can
specify it as a value that evaluates to False to remove the scheme from
the header:
```
authentication_method=HeaderAuthentication(
   token="secret_value"
   parameter="Foo",
   scheme=None,
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
If an error occurs trying to parse to json then a `UnexpectedError`
will be raised.

### `XmlResponseHandler`
Handler that parses the response data to an `xml.etree.ElementTree.Element`.
If an error occurs trying to parse to xml then a `UnexpectedError`
will be raised.

### `YamlResponseHandler`
Handler that parses the response data in `yaml` format and returns the
dictionary.  If an error occurs trying to parse the yaml then an `UnexpectedError`
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

The exception handling for `api-client` has been designed in a way so that all exceptions inherit from
one base exception type: `APIClientError`.  From there, the exceptions have been broken down into the
following categories:

### `ResponseParseError`

Something went wrong when trying to parse the successful response into the defined format.  This could be due
to a misuse of the ResponseHandler, i.e. configuring the client with an `XmlResponseHandler` instead of
a `JsonResponseHandler`

### `APIRequestError`

Something went wrong when making the request.  These are broken down further into the following categories to provide
greater granularity and control.

#### `RedirectionError`
A redirection status code (3xx) was returned as a final code when making the
request. This means that no data can be returned to the client as we could
not find the requested resource as it had moved.


### `ClientError`
A clienterror status code (4xx) was returned when contacting the API. The most common cause of
these errors is misuse of the client, i.e. sending bad data to the API.


### `ServerError`
The API was unreachable when making the request.  I.e. a 5xx status code.


### `UnexpectedError`
An unexpected error occurred when using the client.  This will typically happen when attempting
to make the request, for example, the client never receives a response.  It can also occur to
unexpected status codes (>= 600).


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