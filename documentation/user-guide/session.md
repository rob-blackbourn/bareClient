# Session

A session utility `HttpSession` is provided.

The 

```python
import asyncio
import logging

import bareutils.response_code as response_code
from bareclient import HttpSession

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    session = HttpSession('http://localhost:9009')
    for path in ['/example1', '/example2', '/empty']:
        async with session.request(path, method='GET') as response:
            print(response)
            if not response_code.is_successful(response['status_code']):
                print("failed")
            else:
                if response['status_code'] == response_code.OK and response['more_body']:
                    async for part in response['body']:
                        print(part)


asyncio.run(main())
```

The session object will maintain cookies.
