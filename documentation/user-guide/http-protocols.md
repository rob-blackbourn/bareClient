# HTTP Protocols

Currently the client understands HTTP/1.1 and HTTP/2.

The protocols can set with an optional argument `protocols`, which is set to
`DEFAULT_PROTOCOLS` by default. For example to restrict the client to HTTP/2:

```python
import asyncio
from bareclient import HttpClient, DEFAULT_CIPHERS

async def main(url: str) -> None:
    async with HttpClient(url, method='GET', protocols=['h2']) as response:
        print(response)
        if response.status_code == 200 and response.body is not None:
            async for part in response.body:
                print(part)
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```
