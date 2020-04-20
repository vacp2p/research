#import libp2p/protocols/pubsub/floodsub
#import unittest, sequtils
#import nimbus/rpc/waku
## example.nim

import chronos
import libp2p/standard_setup
import libp2p/[switch,
               crypto/crypto,
               protocols/pubsub/pubsub,
               protocols/pubsub/rpc/messages,
               protocols/pubsub/rpc/message]
import ../vendor/nimbus/waku/wakunode

# From tests/pubsub/utils.nim
proc generateNodes*(num: Natural, gossip: bool = false): seq[Switch] =
  for i in 0..<num:
    result.add(newStandardSwitch(gossip = gossip))

proc subscribeNodes*(nodes: seq[Switch]) {.async.} =
  var dials: seq[Future[void]]
  for dialer in nodes:
    for node in nodes:
      if dialer.peerInfo.peerId != node.peerInfo.peerId:
        dials.add(dialer.connect(node.peerInfo))
  await sleepAsync(100.millis)
  await allFutures(dials)

# Basic in-proc test
proc runTest(): Future[bool] {.async.} =
  var completionFut = newFuture[bool]()
  proc handler(topic: string, data: seq[byte]) {.async, gcsafe.} =
    echo "Handler hit with topic " & topic
    assert topic == "foobar"
    completionFut.complete(true)

  var nodes = generateNodes(2)
  var awaiters: seq[Future[void]]
  awaiters.add((await nodes[0].start()))
  awaiters.add((await nodes[1].start()))

  await subscribeNodes(nodes)
  echo "Node B subscribing to topic 'foobar'"
  await nodes[1].subscribe("foobar", handler)
  await sleepAsync(1000.millis)

  echo "Node A publishing on topic 'foobar'"
  await nodes[0].publish("foobar", cast[seq[byte]]("Hello!"))

  result = await completionFut
  await allFutures(nodes[0].stop(), nodes[1].stop())
  await allFutures(awaiters)

when isMainModule:
  echo("Hello, World!")
  discard waitFor runTest()
