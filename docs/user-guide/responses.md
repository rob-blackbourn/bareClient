# Responses

The response is yielded in the `HttpClient` async context.

See the api reference for the documentation of the (`Response`)[/api/bareclient/#class-response]
class.

## Response Body

The response body (`response.body`) may be `None` or an async iterator. It can be
iterated over asynchronously as follows.

```python
async for part in response.body:
    print(part)
```

The response body is only available in the context of the response, and can only
be read once.
