# Responses

The response is yielded in the `HttpClient` async context.

The response object has the following fields:

Fields:

- **`status_code`** (_int_) - The HTTP status code.
- **`headers`** (_List[[byte string, byte string]]_) - A list of [name,
  value] two-item iterables, where name is the header name, and value is the
  header value. Order must be preserved in the HTTP response. Header names
  must be lowercased. Optional; defaults to an empty list. Pseudo headers
  (present in HTTP/2 and HTTP/3) must not be present.
- **`body`** (_Optional[AsyncIterable[byte string]]_) - The body content if any.

## Response Body

The response body (`response.body`) may be `None` or an async iterator. It can be
iterated over asynchronously as follows.

```python
async for part in response.body:
    print(part)
```
