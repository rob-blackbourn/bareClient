Lightweight Asyncio HTTP Client
===============================

A simple asyncio http client.

Description
-----------

This package provides the asyncio transport for `h11 <https://h11.readthedocs.io/en/latest/index.html>`_.

It makes little attempt to provide any helpful features.

This client is part of a suite of lightweight HTTP tools around the `bareASGI <https://bareasgi.readthedocs.io/en/latest/index.html>`_ framework.

Installation
------------

This is a Python 3.7 package.

.. code-block:: bash

    pip install bareclient

Usage
-----

The basic usage is to create an ``HttpClient``.

.. code-block:: python

    import asyncio
    from bareclient import HttpClient
    import ssl


    async def main(url, headers, ssl):
        async with HttpClient(url, method='GET', headers=headers, ssl=ssl) as (response, body):
            print(response)
            if response.status_code == 200:
                async for part in body:
                    print(part)


    url = 'https://docs.python.org/3/library/cgi.html'
    headers = [(b'host', b'docs.python.org'), (b'connection', b'close')]
    ssl_context = ssl.SSLContext()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(url, headers, ssl_context))


There is also an ``HttpSession`` for keep-alive connections.

.. code-block:: python

    import asyncio
    import logging

    import bareutils.response_code as response_code
    from bareclient import HttpSession

    logging.basicConfig(level=logging.DEBUG)


    async def main() -> None:
        session = HttpSession(
            'https://shadow.jetblack.net:9009',
            capath='/etc/ssl/certs'
        )
        headers = [
            (b'host', b'shadow.jetblack.net'),
            (b'connection', b'close')
        ]
        for path in ['/example1', '/example2', '/empty']:
            async with session.request(path, method='GET', headers=headers) as (response, body):
                print(response)
                if not response_code.is_successful(response['status_code']):
                    print("failed")
                else:
                    if response['status_code'] == response_code.OK:
                        async for part in body:
                            print(part)


    asyncio.run(main())

Finally there is a single helper function to get json.

.. code-block:: python

    import asyncio
    import ssl
    from bareclient import get_json


    async def main(url, ssl):
        obj = await get_json(url, ssl=ssl)
        print(obj)


    url = 'https://jsonplaceholder.typicode.com/todos/1'
    ssl_context = ssl.SSLContext()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(url, ssl_context))


.. toctree::
    :maxdepth: 2
    :caption: Contents:

    api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`