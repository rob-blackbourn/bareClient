# Requests

## HttpClient

The request is specified in the arguments to `HttpClient`.

The first argument is the `url`. The remaining are keyword arguments:

Keyword arguments:

- **`method`** (`str`, optional): The HTTP method. Defaults to 'GET'.
- **`headers`** (`Optional[Sequence[Tuple[bytes, bytes]]]`, optional): The headers. Defaults to
  None.
- **`body`** (`Optional[AsyncIterable[bytes]]`, optional): The body content. Defaults to
  None.
- **`middleware`** (`Optional[List[HttpClientMiddlewareCallback]]`, optional): The
  middleware. Defaults to None.
- **`config`** (`Optional[HttpClientConfig]`, optional): The client config. Defaults to None.

### `HttpClientConfig`

Keywork arguments:

- **`h11_bufsiz`** (int, optional): The HTTP/1 buffer size. Defaults to 8096.
- **`cafile`** (Optional[str], optional): The path to a file of concatenated
  CA certificates in PEM format. Defaults to None.
- **`capath`** (Optional[str], optional): The path to a directory containing
  several CA certificates in PEM format. Defaults to None.
- **`cadata`** (Optional[str], optional): Either an ASCII string of one or
  more PEM-encoded certificates or a bytes-like object of
  DER-encoded certificates. Defaults to None.
- **`ssl_context`** (`Optional[SSLContext]`, optional): An explicit SSL context to use for the connection. Defaults to None.
- **`alpn_protocols`** (Optional[List[str]], optional): The alpn_protocols.
  Defaults to None.
- **`ciphers`** ('Iterable[str]', optional): The ciphers to use in an SSL connection. Defaults to `DEFAULT_CIPHERS`.
