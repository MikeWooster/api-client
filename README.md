[![Unit Tests](https://github.com/MikeWooster/api-client/actions/workflows/test.yml/badge.svg)](https://github.com/MikeWooster/api-client/actions/workflows/test.yml)

# Note to users of this API

To those that have been paying attention to the commit history will note that
I have had no time to actively maintain this library.  If there are any volunteers
to continue the development of this library, I would be happy to add you as
contributors.  Please get in touch, and I will try to sort out a group to continue
this development.  Also note, that my reply time may not be that timely, so please
be patient.

# Python API Client

A client for communicating with an api should be a clean abstraction
over the third part api you are communicating with. It should be easy to
understand and have the sole responsibility of calling the endpoints and
returning data.

To achieve this, `APIClient` takes care of the other (often duplicated)
responsibilities, such as authentication and response handling, moving
that code away from the clean abstraction you have designed.

## Quick links
1. [Installation](#Installation)
2. [Client in action](#Usage)
3. [Adding retries to requests](#Retrying)
4. [Working with paginated responses](#Pagination)
5. [Authenticating your requests](#Authentication-Methods)
6. [Handling the formats of your responses](#Response-Handlers)
7. [Correctly encoding your outbound request data](#Request-Formatters)
8. [Handling bad requests and responses](#Exceptions)
9. [Endpoints as code](#Endpoints)
10. [Extensions](#Extensions)
11. [Roadmap](#Roadmap)

## Installation

```bash
pip install api-client
```

## Usage

### Simple Example
```python
from apiclient import APIClient

class MyClient(APIClient):

    def list_customers(self):
        url = "http://example.com/customers"
        return self.get(url)

    def add_customer(self, customer_info):
        url = "http://example.com/customers"
        return self.post(url, data=customer_info)

>>> client = MyClient()
>>> client.add_customer({"name": "John Smith", "age": 28})
>>> client.list_customers()
[
    ...,
    {"name": "John Smith", "age": 28},
]
```
The `APIClient` exposes a number of predefined methods that you can call
This example uses `get` to perform a GET request on an endpoint.
Other methods include: `post`, `put`, `patch` and `delete`. More
information on these methods is documented in the [Interface](#APIClient-Interface).


For a more complex use case example, see: [Extended example](#Extended-Example)

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

```python
from apiclient import retry_request

class MyClient(APIClient):

    @retry_request
    def retry_enabled_method():
        ...

```

For more complex use cases, you can build your own retry decorator using
tenacity along with the custom retry strategy.

For example, you can build a retry decorator that retries `APIRequestError`
which waits for 2 seconds between retries and gives up after 5 attempts.

```python
import tenacity
from apiclient.retrying import retry_if_api_request_error

retry_decorator = tenacity.retry(
    retry=retry_if_api_request_error(),
    wait=tenacity.wait_fixed(2),
    stop=tenacity.stop_after_attempt(5),
    reraise=True,
)
```

Or you can build a decorator that will retry only on specific status
codes (following a failure).

```python
retry_decorator = tenacity.retry(
    retry=retry_if_api_request_error(status_codes=[500, 501, 503]),
    wait=tenacity.wait_fixed(2),
    stop=tenacity.stop_after_attempt(5),
    reraise=True,
)
```


## Pagination

In order to support contacting pages that respond with multiple pages of data when making get requests,
add a `@paginated` decorator to your client method.  `@paginated` can paginate the requests either where
the pages are specified in the query parameters, or by modifying the url.

Usage is simple in both cases; paginator decorators take a Callable with two required arguments:
- `by_query_params` -> callable takes `response` and `previous_page_params`.
- `by_url` -> callable takes `respones` and `previous_page_url`.

The callable will need to return either the params in the case of `by_query_params`, or a new url in the
case of `by_url`.
If the response is the last page, the function should return None.

Usage:

```python
from apiclient.paginators import paginated


def next_page_by_params(response, previous_page_params):
    # Function reads the response data and returns the query param
    # that tells the next request to go to.
    return {"next": response["pages"]["next"]}


def next_page_by_url(response, previous_page_url):
    # Function reads the response and returns the url as string
    # where the next page of data lives.
    return response["pages"]["next"]["url"]


class MyClient(APIClient):

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
```python
client = ClientImplementation(
   authentication_method=<AuthenticationMethodClass>(),
   response_handler=...,
   request_formatter=...,
)
```

### `NoAuthentication`
This authentication method simply does not add anything to the client,
allowing the api to contact APIs that do not enforce any authentication.

Example:
```python
client = ClientImplementation(
   authentication_method=NoAuthentication(),
   response_handler=...,
   request_formatter=...,
)
```

### `QueryParameterAuthentication`
This authentication method adds the relevant parameter and token to the
client query parameters.  Usage is as follows:

```python
client = ClientImplementation(
    authentication_method=QueryParameterAuthentication(parameter="apikey", token="secret_token"),
    response_handler=...,
    request_formatter=...,
)
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
```python
client = ClientImplementation(
    authentication_method=HeaderAuthentication(token="secret_value"),
    response_handler=...,
    request_formatter=...,
)

# Constructs request header:
{"Authorization": "Bearer secret_value"}
```
The `Authorization` parameter and `Bearer` scheme can be adjusted by
specifying on method initialization.
```python
authentication_method=HeaderAuthentication(
   token="secret_value"
   parameter="apikey",
   scheme="Token",
)

# Constructs request header:
{"apikey": "Token secret_value"}
```

Or alternatively, when APIs do not require a scheme to be set, you can
specify it as a value that evaluates to False to remove the scheme from
the header:
```python
authentication_method=HeaderAuthentication(
   token="secret_value"
   parameter="token",
   scheme=None,
)

# Constructs request header:
{"token": "secret_value"}
```

Additional header values can be passed in as a dict here when API's require more than one
header to authenticate:
```python
authentication_method=HeaderAuthentication(
   token="secret_value"
   parameter="token",
   scheme=None,
   extra={"more": "another_secret"}
)

# Constructs request header:
{"token": "secret_value", "more": "another_secret"}
```

### `BasicAuthentication`
This authentication method enables specifying a username and password to APIs
that require such.
```python
client = ClientImplementation(
    authentication_method=BasicAuthentication(username="foo", password="secret_value"),
    response_handler=...,
    request_formatter=...,
)
```

### `CookieAuthentication`
This authentication method allows a user to specify a url which is used
to authenticate an initial request, made at APIClient initialization,
with the authorization tokens then persisted for the duration of the
client instance in cookie storage.

These cookies use the `http.cookiejar.CookieJar()` and are set on the
session so that all future requests contain these cookies.

As the method of authentication at the endpoint is not standardised
across API's, the authentication method can be customized using one of
the already defined authentication methods; `QueryParameterAuthentication`,
`HeaderAuthentication`, `BasicAuthentication`.

```python
client = ClientImplementation(
    authentication_method=(
        CookieAuthentication(
            auth_url="https://example.com/authenticate",
            authentication=HeaderAuthentication("1234-secret-key"),
        ),
    response_handler=...,
    request_formatter=...,
)
```

## Response Handlers

Response handlers provide a standard way of handling the final response
following a successful request to the API.  These must inherit from
`BaseResponseHandler` and implement the `get_request_data()` method which
will take the `requests.Response` object and parse the data accordingly.

The apiclient supports the following response handlers, by specifying
the class on initialization of the client as follows:

The response handler can be omitted, in which case no formatting is applied to the
outgoing data.

```python
client = ClientImplementation(
   authentication_method=...,
   response_handler=<ResponseHandlerClass>,
   request_formatter=...,
)
```

### `RequestsResponseHandler`
Handler that simply returns the original `Response` object with no
alteration.

Example:
```python
client = ClientImplementation(
    authentication_method=...,
    response_handler=RequestsResponseHandler,
    request_formatter=...,
)
```

### `JsonResponseHandler`
Handler that parses the response data to `json` and returns the dictionary.
If an error occurs trying to parse to json then a `ResponseParseError`
will be raised.

Example:
```python
client = ClientImplementation(
    authentication_method=...,
    response_handler=JsonResponseHandler,
    request_formatter=...,
)
```

### `XmlResponseHandler`
Handler that parses the response data to an `xml.etree.ElementTree.Element`.
If an error occurs trying to parse to xml then a `ResponseParseError`
will be raised.

Example:
```python
client = ClientImplementation(
    authentication_method=...,
    response_handler=XmlResponseHandler,
    request_formatter=...,
)
```

## Request Formatters

Request formatters provide a way in which the outgoing request data can
be encoded before being sent, and to set the headers appropriately.

These must inherit from `BaseRequestFormatter` and implement the `format()`
method which will take the outgoing `data` object and format accordingly
before making the request.

The apiclient supports the following request formatters, by specifying
the class on initialization of the client as follows:

```python
client = ClientImplementation(
   authentication_method=...,
   response_handler=...,
   request_formatter=<RequestFormatterClass>,
)
```

### `JsonRequestFormatter`

Formatter that converts the data into a json format and adds the
`application/json` Content-type header to the outgoing requests.


Example:
```python
client = ClientImplementation(
    authentication_method=...,
    response_handler=...,
    request_formatter=JsonRequestFormatter,
)
```

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

## Custom Error Handling

Error handlers allow you to customize the way request errors are handled in the application.

Create a new error handler, extending `BaseErrorHandler` and implement the `get_exception`
static method.

Pass the custom error handler into your client upon initialization.

Example:
```python
from apiclient.error_handlers import BaseErrorHandler
from apiclient import exceptions
from apiclient.response import Response

class MyErrorHandler(BaseErrorHandler):

    @staticmethod
    def get_exception(response: Response) -> exceptions.APIRequestError:
        """Parses client errors to extract bad request reasons."""
        if 400 <= response.get_status_code() < 500:
            json = response.get_json()
            return exceptions.ClientError(json["error"]["reason"])
        
        return exceptions.APIRequestError("something went wrong")
        
```
In the above example, you will notice that we are utilising an internal
`Response` object. This has been designed to abstract away the underlying response
returned from whatever strategy that you are using. The `Response` contains the following
methods:

* `get_original`: returns the underlying response object. This has been implemented
for convenience and shouldn't be relied on.
* `get_status_code`: returns the integer status code.
* `get_raw_data`: returns the textual data from the response.
* `get_json`: should return the json from the response.
* `get_status_reason`: returns the reason for any HTTP error code.
* `get_requested_url`: returns the url that the client was requesting.

## Request Strategy

The design of the client provides a stub of a client, exposing the required methods; `get`, 
`post`, etc. And this then calls the implemented methods of a request strategy.

This allows us to swap in/out strategies when needed. I.e. you can write your own
strategy that implements a different library (e.g. `urllib`). Or you could pass in a
mock strategy for testing purposes.

Example strategy for testing:
```python
from unittest.mock import Mock

from apiclient import APIClient
from apiclient.request_strategies import BaseRequestStrategy

def test_get_method():
    """test that the get method is called on the underlying strategy.
    
    This does not execute any external HTTP call.
    """
    mock_strategy = Mock(spec=BaseRequestStrategy)
    client = APIClient(request_strategy=mock_strategy)
    client.get("http://google.com")
    mock_strategy.get.assert_called_with("http://google.com", params=None)
```

## Endpoints

The apiclient also provides a convenient way of defining url endpoints with
use of the `@endpoint` decorator.  In order to decorate a class with `@endpoint`
the decorated class must define a `base_url` attribute along with the required
resources.  The decorator will combine the base_url with the resource.

Example:

```python
from apiclient import endpoint

@endpoint(base_url="http://foo.com")
class Endpoint:
    resource = "search"

>>> Endpoint.resource
"http://foo.com/search"
```

## Extensions

### Marshalling JSON

[api-client-jsonmarshal](https://github.com/MikeWooster/api-client-jsonmarshal): automatically
marshal to/from JSON into plain python dataclasses. Full usage examples can be found in the extensions home page.

### Pydantic

[api-client-pydantic](https://github.com/mom1/api-client-pydantic): validate request data and converting json straight 
to pydantic class.

## Extended Example

```python
from apiclient import (
    APIClient,
    endpoint,
    paginated,
    retry_request,
    HeaderAuthentication,
    JsonResponseHandler,
    JsonRequestFormatter,
)
from apiclient.exceptions import APIClientError

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
class JSONPlaceholderClient(APIClient):

    @paginated(by_query_params=get_next_page)
    def get_all_todos(self) -> dict:
        return self.get(Endpoint.todos)

    @retry_request
    def get_todo(self, todo_id: int) -> dict:
        url = Endpoint.todo.format(id=todo_id)
        return self.get(url)


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
# NotFound: 404 Error: Not Found for url: https://jsonplaceholder.typicode.com/todos/450

>>> try:
...     client.get_todo(450)
... except APIClientError:
...     print("All client exceptions inherit from APIClientError")
"All client exceptions inherit from APIClientError"

```

## APIClient Interface
The `APIClient` provides the following public interface:
* `post(self, endpoint: str, data: dict, params: OptionalDict = None)`

   Delegate to POST method to send data and return response from endpoint.

* `get(endpoint: str, params: OptionalDict = None)`

   Delegate to GET method to get response from endpoint.

* `put(endpoint: str, data: dict, params: OptionalDict = None)`

   Delegate to PUT method to send and overwrite data and return response from endpoint.

* `patch(endpoint: str, data: dict, params: OptionalDict = None)`

   Delegate to PATCH method to send and update data and return response from endpoint

* `delete(endpoint: str, params: OptionalDict = None)`

   Delegate to DELETE method to remove resource located at endpoint.

* `get_request_timeout() -> float`

   By default, all requests have been set to have a default timeout of 10.0 s.  This
   is to avoid the request waiting forever for a response, and is recommended
   to always be set to a value in production applications.  It is however possible to
   override this method to return the timeout required by your application.

## Mentions

Many thanks to [JetBrains](https://www.jetbrains.com/?from=api-client) for supplying me with a license to use their product in the development
of this tool.

![JetBrains](readme-data/jetbrains.svg)

## Roadmap

1. Enable async support for APIClient.
