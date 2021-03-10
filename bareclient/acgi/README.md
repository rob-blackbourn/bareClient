# ACGI

This is an attempt to implement an [ASGI](https://asgi.readthedocs.io/en/latest/)
style interface for the client.

This is very much work in progress.

## Messages

### Request

Sent from the client to ACGI.

* `type` (Unicode String) - `"http.request"`
* `url` (Unicode String) - The requested url
* `method` (Unicode string) - The HTTP request method
* `headers` (Iterable[[byte string, byte string]]) – An iterable of [name, value] two-item iterables, where name is the header name, and value is the header value. 
* `body` (byte string) - The body of the request.
* `more_body` (bool) - If `True` there is more body, otherwise `False`

### Request Connection

Sent from the client to ACGI.

* `type` (Unicode string) - `"http.response.connection"`
* `http_version` (Unicode string) - Either `"h11"` or `"h2"`.
* `stream_id` (Optional[int]) - The stream id for an h2 connection

The `stream_id` is used for subsequent communication.

### Request Body

Sent from the client to ACGI.

* `type` (Unicode string) - `"http.request.body"`
* `body` (byte string) - The body of the request
* `more_body` (bool) - If `True` there is more body, otherwise `False`
* `stream_id` (Optional int) - The stream id for h2 requests

### Response

Sent from the ACGI to the client.

* `type` (Unicode string) - `"http.response"`
* `acgi` (Dict[str, str]) `{ "version": "1.0" }`
* `http_version` (Unicode string) - `"2"`
* `status_code` (int) - The status code
* `headers` (Iterable[[byte string, byte string]]) – An iterable of [name, value] two-item iterables, where name is the header name, and value is the header value. 
* `more_body` (bool) - `True` if there is more body to read, otherwise `False`
* `body` (AsyncGenerator[bytes]) - The body
* `stream_id` (Optional[int]) - The stream id for the response for an h2 connection.

### Response Body

Sent from the ACGI to the client.

* `type` (Unicode string) - `"http.response.body"`
* `body` (bytes) - The body
* `more_body` (bool) - `True` if there is more body to receive otherwise `False`
* `stream_id` (Optional[int]) - An optional stream id

### Disconnect

Sent from either the client or ACGI.

* `type` (Unicode string) - `"http.stream.disconnect"`
* `stream_id` (Optional[int]) - The stream id for the response for an h2 connection.
