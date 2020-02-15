# Client

The basic usage is to create an `HttpClient`.

## GET

The following example demonstrates a simple `GET` request.

```python
import asyncio
from bareclient import HttpClient


async def main(url: str) -> None:
    async with HttpClient(url) as response:
        if response['status_code'] == 200 and response['more_body']:
            async for part in response['body']:
                print(part)


asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```

The `HttpClient` provides an async context yielding a response or type
`Mapping[str, Any]` which loosely follows the semantics of ASGI message
passing.

## Request

The request is specified in the arguments to `HttpClient`.

The first argument is the `url`. The remaining are keyword arguments:

Keyword arguments:

* **`method`** (str, optional): The HTTP method. Defaults to 'GET'.
* **`headers`** (Optional[List[Header]], optional): The headers. Defaults to
    None.
* **`content`** (Optional[Content], optional): The body content. Defaults to
    None.
* **`loop`** (Optional[AbstractEventLoop], optional): The optional asyncio
    event loop. Defaults to None.
* **`h11_bufsiz`** (int, optional): The HTTP/1 buffer size. Defaults to
    8096.
* **`cafile`** (Optional[str], optional): The path to a file of concatenated
    CA certificates in PEM format. Defaults to None.
* **`capath`** (Optional[str], optional): The path to a directory containing
    several CA certificates in PEM format. Defaults to None.
* **`cadata`** (Optional[str], optional): Either an ASCII string of one or
    more PEM-encoded certificates or a bytes-like object of
    DER-encoded certificates. Defaults to None.
* **`decompressors`** (Optional[Mapping[bytes, Type[Decompressor]]], optional):
    The decompressors. Defaults to None.
* **`protocols`** (Optional[List[str]], optional): The protocols. Defaults
    to None.


## Response

The response is yielded in the `HttpClient` async context.

Keys:

* **`type`** (*Unicode string*) - Currently the only response is
    `"http.response"`.
* **`acgi["version"]`** (*Unicode string*) - Version of the ACGI spec.
* **`http_version`** (*Unicode string*) - One of `"1.0"`, `"1.1"` or `"2"`.
* **`stream_id`** (*int*) - The HTTP/2 stream id, otherwise None.
* **`status_code`** (*int*) - The HTTP status code.
* **`headers`** (*Iterable[[byte string, byte string]]*) - A iterable of [name,
    value] two-item iterables, where name is the header name, and value is the
    header value. Order must be preserved in the HTTP response. Header names
    must be lowercased. Optional; defaults to an empty list. Pseudo headers
    (present in HTTP/2 and HTTP/3) must not be present.
* **`more_body`** (*bool*) - Signifies if the body has more content.
* **`body`** (*AsyncIterable[byte string]*) - The body content.

For the above request the response might look as follows:

```python
{
    'type': 'http.response',
    'acgi': {'version': '1.0'}, 
    'http_version': '2',
    'stream_id': 1,
    'status_code': 200,
    'headers': [
        (b'content-type', b'text/html'),
        (b'content-length', b'53727'),
        (b'last-modified', b'Sat, 15 Feb 2020 0...26:32 GMT'),
        ...
    ],
    'more_body': True,
    'body': <async_generator obj...5ede8f320>, 
}
```

## Response Body

The response body (`response["body"]`) can be iterated over asynchronusly.

```python
async for part in response['body']:
    print(part)
```
