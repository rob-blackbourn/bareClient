# Responses

The response is yielded in the `HttpClient` async context.

Keys:

- **`type`** (_Unicode string_) - Currently the only response is
  `"http.response"`.
- **`acgi["version"]`** (_Unicode string_) - Version of the ACGI spec.
- **`http_version`** (_Unicode string_) - One of `"1.0"`, `"1.1"` or `"2"`.
- **`stream_id`** (_int_) - The HTTP/2 stream id, otherwise None.
- **`status_code`** (_int_) - The HTTP status code.
- **`headers`** (_Iterable[[byte string, byte string]]_) - A iterable of [name,
  value] two-item iterables, where name is the header name, and value is the
  header value. Order must be preserved in the HTTP response. Header names
  must be lowercased. Optional; defaults to an empty list. Pseudo headers
  (present in HTTP/2 and HTTP/3) must not be present.
- **`more_body`** (_bool_) - Signifies if the body has more content.
- **`body`** (_AsyncIterable[byte string]_) - The body content.

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
