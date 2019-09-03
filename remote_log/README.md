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


## Sketching interface

NS POST <>
NS GET <>

CAS POST <>
CAS GET <>

What's in <>?

- hash string
- blob
- [[h1_3, h2_3], [h1_2, h2_2]], next_page_chunk]

- How do we want to encode this?
- Or we can use protobuf or json
- This seems mostly relevant for ns_head

- lets just start with json thingy and NS/CAS sep


HASH1 and HASH2, all that matters. HASH1 is native for MVDS message (name?) and
HASH2 native to the remote log CAS.

For NS, we want to know how to update it in/communicate it.

And then actual format with mapping and paging, in a way that's adjustable, and
so on.

Can we generalize this to pack file for backups? Ie type and pointer to more etc

This would allow to go download whole thingy

also support many remote logs kind of thing, default or w/e

can we remove? scrub somehow.

### Protobuf next

Actually use them, and check enum and dispatching etc.


##  Deps

Put in Makefile

nimble install https://github.com/PMunch/protobuf-nim

### Protobuf service generation
Install `nimtwirp`, then:
`nimtwirp_build  -I:. --out:. protocol.proto `
