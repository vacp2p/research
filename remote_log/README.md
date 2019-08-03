# Remote log mocking

Using socket server and client in Nim to mimick behavior of a remote log for
data sync.

See https://notes.status.im/Rwh-18AdSgKAkhfwfBE-OA# for current sketch. More
full spec to come.

## Interfaces

A server represents a remote log. A client is an endpoint.

We need something to represent storage as well.

TODO: Break down roles into individual actors as scripts.

### Node

Represents an endpoint, like a data sync node. Multiple actors.

Outside of using transport to send "live" messages (outside of scope here), it
also uploads them to CAS and NS. Flow looks different for sending node and
reciving node.

Sending node flow:
1. CAS Update
2. NS Update

Receiving node flow:
1. NS fetch
2. CAS fetch

Details to come.

### Name system (NS)

E.g. DNS/ENS/Feeds. Fixed name for mutable resoures.

Supports which operations:

- `Update name with data => Ok/Error`
- `Fetch name => data`

### Content-addressed storage (CAS)

Request/response interface for immutable data.

Supports two operations:

- `Upload data => id`
- `Fetch id => data`
