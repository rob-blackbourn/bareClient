# Requests

## HttpClient

The request is specified in the arguments to `HttpClient`.

The first argument is the `url`. The remaining are keyword arguments:

Keyword arguments:

- **`method`** (str, optional): The HTTP method. Defaults to 'GET'.
- **`headers`** (Optional[List[Header]], optional): The headers. Defaults to
  None.
- **`content`** (Optional[Content], optional): The body content. Defaults to
  None.
- **`loop`** (Optional[AbstractEventLoop], optional): The optional asyncio
  event loop. Defaults to None.
- **`h11_bufsiz`** (int, optional): The HTTP/1 buffer size. Defaults to 8096.
- **`cafile`** (Optional[str], optional): The path to a file of concatenated
  CA certificates in PEM format. Defaults to None.
- **`capath`** (Optional[str], optional): The path to a directory containing
  several CA certificates in PEM format. Defaults to None.
- **`cadata`** (Optional[str], optional): Either an ASCII string of one or
  more PEM-encoded certificates or a bytes-like object of
  DER-encoded certificates. Defaults to None.
- **`protocols`** (Optional[List[str]], optional): The protocols. Defaults
  to None.
- **`middleware`** (Optional[List[HttpClientMiddlewareCallback]], optional): The
  middleware. Defaults to None.

## HttpSession

For an `HttpSession` there is a request method which takes the following arguments:

The first argument is the `path`. The remaining are keyword arguments:

Keyword arguments:

- **`method`** (str, optional): The HTTP method. Defaults to 'GET'.
- **`headers`** (Optional[List[Header]], optional): The headers. Defaults to
  None.
- **`content`** (Optional[Content], optional): The body content. Defaults to
  None.
