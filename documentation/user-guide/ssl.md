# SSL

The [`HttpClient`](/api/bareclient/#class-httpclient),
[`HttpSession`](/api/bareclient/#class-httpsession), and the helper functions
all take a number of optional arguments which may be used to configure SSl.

## SSLContext

If an ssl.SSLContext is passed (e.g. `HttpClient(... , ssl_context=ctx)`) all
other arguments are ignored.

There a two helper functions.

- create_ssl_context - creates a simple ssl context
- create_ssl_context_with_cert_chain - creates a context with a client certificate and key.

## Optional helper arguments

There are a number of helper arguments which are useful for making targeted changes
to the default ssl context.

The arguments `cafile`, `capath`, and `cadata` are passed directly though to
[ssl.create_default_context](https://docs.python.org/3/library/ssl.html#ssl.create_default_context).

The argument `ciphers` is an iterable that defaults to `DEFAULT_CIPHERS`. It is
applied to the
[`SSLContext`](https://docs.python.org/3/library/ssl.html#ssl.SSLContext)
instance with
[`set_ciphers`](https://docs.python.org/3/library/ssl.html#ssl.SSLContext.set_ciphers).
The following shows how to downgrade the security level for trusted legacy
servers.

```python
import asyncio
from bareclient import HttpClient, DEFAULT_CIPHERS


async def main(url: str) -> None:
    ciphers = list(DEFAULT_CIPHERS) + ['ALL:@SECLEVEL=1']
    async with HttpClient(url, method='GET', ciphers=ciphers) as response:
        print(response)
        if response.status_code == 200 and response.body:
            async for part in response.body:
                print(part)
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```

The argument `options` is an iterable of SSL options which are applied as an "or"
to the
[`SSLContext.options](https://docs.python.org/3/library/ssl.html#ssl.SSLContext.set_ciphers)
member variable. By default it is set to `DEFAULT_OPTIONS` which is a tuple of
options which seemed sensible at the time this library was built.
