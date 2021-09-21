# Welcome

A simple asyncio http Pyhton client package supporting HTTP versions 1.0, 1.1
and 2.

This is the client companion to the ASGI server side web framework
[bareASGI](https://github.com/rob-blackbourn/bareASGI) and follows the same
"bare" approach. It makes little attempt to provide any helpful features which
might do unnecessary work, providing a foundation for whatever feature set is
required.

It was written to allow a web server which had negotiated the HTTP/2 protocol
for make outgoing HTTP/2 calls. This increases performance and simplifies proxy
configuration in a micro-service architecture.

To find out more see [getting started](user-guide/getting-started.md).
