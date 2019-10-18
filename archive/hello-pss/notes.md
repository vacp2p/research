# Misc notes

Dumping ground of CLI commands and debugging.

## Swarm hello world

```
# Geth new account
geth account new
echo "0ab9f275308307188de76f82cbc08a5258b03110" >> alice.tmp

# Get rid of password prompt later
echo "" >> password.tmp

# Start swarm node
swarm --bzzaccount `cat alice.tmp`

# Test up and down
swarm up README.md > readme-ref.tmp
swarm down bzz:/`cat readme-ref.tmp` test.tmp
```

## Feeds

```
# Using human readable topic, can equally well use --topic
swarm --bzzaccount `cat alice.tmp` feed create --name "bob"
# Returns feed manifest
# 2a0ddb7d63cc4926d168697da1ad76bdad3782611c8f75bd1ce2f8b5e096b6e0

# XXX: What's the difference? Doesn't it use bzzapi and use local instance by default?
swarm --bzzaccount `cat alice.tmp` --bzzapi http://localhost:8500 feed create --name "bob"
# 2a0ddb7d63cc4926d168697da1ad76bdad3782611c8f75bd1ce2f8b5e096b6e0

# XXX: What to do with feed manifest? How get it?

# Posting to a feed using name/topic/manifest, need hex, example here
swarm --bzzaccount `cat alice.tmp` feed update --name bob 0x68656c6c6f2031

# Reading feed info 
swarm --bzzaccount `cat alice.tmp` feed info --name "bob"
# {"feed":{"topic":"0x626f620000000000000000000000000000000000000000000000000000000000","user":"0x0ab9f275308307188de76f82cbc08a5258b03110"},"epoch":{"time":1554695168,"level":24},"protocolVersion":0}

# Reading feed updates, can't with CLI but
curl 'http://localhost:8500/bzz-feed:/?user=0x0ab9f275308307188de76f82cbc08a510&name=bob'
# `hello 1` = hex above? +1

# Posting message to feed 
echo "Hello world" > message
# Need right format for hex
cat message | hexdump -v -e '/1 "%02x"' > hex-message

swarm --bzzaccount `cat alice.tmp` --password password.tmp feed update --name bob 0x`cat hex-message`

curl 'http://localhost:8500/bzz-feed:/?user=0x0ab9f275308307188de76f82cbc08a5258b03110&name=bob'
# Hello world
```

We can use `--user` to refer to another person as opposed to `bzzaccount` by default.

## PSS

First, standalone with ethereum-samples. Second, in Go script send and receive (WIP).

Testing only: private keys galore

Ok we have two (hardcoded) independent, locally running Geth nodes with swarm service messaging over PSS:

```
Received message Hello world from 307830346335363133316438646564393065373962373662393766323665386663303332353937383836666636386162363535376639316334626631616534366561623934343135633664663330626236343739636634306638313139373762623262323337373837663562383037643937313931663761393934613535383633336530
```

### How to run
```
# Run receiver
./scripts/run-bob 

# Run sender
 ./scripts/run-alice
```

### Troubleshooting

To see connected peers:
`geth attach .data_9600/bzz.ipc --exec 'admin.peers'`


For som reason I can attach to 9600 but not 9601 after adding peers:
```
Fatal: Failed to start the JavaScript console: api modules: context deadline exceeded
```

```
DEBUG[04-10|16:45:08.428] Resolving node failed                    id=0x869830         newdelay=2m0s caller=dial.go:333
DEBUG[04-10|16:45:08.630] fetcher request hop count limit reached  hops=20 caller=fetcher.go:162
DEBUG[04-10|16:45:09.004] ChunkStore.Get can not retrieve chunk    peer=b4425dfb4fed04248b4a2ef1eb9a9253b8685a6d4775e2d6264762d8cc8b1a60 addr=c5e800bb76ca919e601440a1192fd94bfbd6e461b9921460272e258aaabb53ab                                                                                                                                                                            hopcount=16 err="context deadline exceeded"            caller=delivery.go:177
DEBUG[04-10|16:45:09.038] ChunkStore.Get can not retrieve chunk    peer=b4425dfb4fed04248b4a2ef1eb9a9253b8685a6d4775e2d6264762d8cc8b1a60 addr=bfb19b17e25ec9981ba740dffc965635099c4306b9d0d6d19a738bdd5c1a2b68                                                                                                                                                                            hopcount=18 err="context deadline exceeded"            caller=delivery.go:177
INFO [04-10|16:45:09.177] unable to request                        request addr=ae61264cc22c960b62abfcefac8059c6f6ef481dfd972381024967915cfebdea err="no peer found"                        caller=fetcher.go:238
```

```
   ruid=d0ecbecb code=200 time=4.903668ms   caller=middleware.go:83
TRACE[04-10|18:15:29.000] search timed out: requesting             request addr=7e05ce20f890f52f793a9fdb438aeef93b96cbc04e21ebb4e5ea3c6f811c957a doRequest=true  caller=fetcher.go:224
TRACE[04-10|18:15:29.000] Delivery.RequestFromPeers: skip peer     peer id=258ab5a8630d8d9d caller=delivery.go:278
TRACE[04-10|18:15:29.000] Delivery.RequestFromPeers: skip peer     peer id=443030fd43226716 caller=delivery.go:278
INFO [04-10|18:15:29.000] unable to request                        request addr=7e05ce20f890f52f793a9fdb438aeef93b96cbc04e21ebb4e5ea3c6f811c957a err="no peer found"
```

Why is it rskipping peer

Two hypothesis of what's wrong:
- Bad kademlia connectivity, implement health check to inspect
   - can attach swarm and hello pss nodes and diff options, since swarm default seems to propagate basic
      e.g. swarmup ends up on swarm gateway
- Local network shenanighans that only shows up for some flows, need to use external ip or so

### Next steps?
- Put logs elsewhere
- Allow send and receive from both (bg subscribe)?
- Allow interactive message send?
- When sending, also update to feeds
- For feeds, move from curl cli to go/jsonrpc api
- When going online, allow querying of feeds
- In message, also includes message dependencies



## Later

Simple Go CLI
