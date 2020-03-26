import
  random, chronos, sequtils, chronicles, tables, stint, options, std/bitops,
  eth/[keys, rlp, async_utils], eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types, routing_table, encoding],
  eth/p2p/discoveryv5/protocol as discv5_protocol,
  ./utils

const N = 100
type
    NodeArray = array[N, discv5_protocol.Protocol]

proc distanceTo(a, b: NodeId): uint32 =
  let a = a.toBytes
  let b = b.toBytes
  var lz = 0
  for i in countdown(a.len - 1, 0):
    let x = a[i] xor b[i]
    if x == 0:
      lz += 8
    else:
      lz += bitops.countLeadingZeroBits(x)
      break
  return uint32(a.len * 8 - lz)

proc randNode(nodes: NodeArray): Node =
    randomize()
    result = nodes[rand(N - 1)].localNode

proc run() {.async.} =
    var nodes: NodeArray

    for i in 0..<N:
        let node = initDiscoveryNode(newPrivateKey(), localAddress(20300 + i), if i > 0: @[nodes[0].localNode.record] else: @[])
        node.start()
        nodes[i] = node

    echo "Setup ", N, " nodes"

    echo "Sleeping for 50 seconds"
    await sleepAsync(50.seconds)

    let target = randNode(nodes)

    let node = initDiscoveryNode(newPrivateKey(), localAddress(20300 + N), @[nodes[0].localNode.record])

    var peer = randNode(nodes)
    block outer:
        while true:
            let lookup = await node.findNode(peer, 256) # @TODO 256 should be replaced with distance between peer and target

            var closest = 256
            for n in items(lookup):
                if n == target:
                    echo "Found ", n.toUri()
                    break outer

                let distance = distanceTo()
                if distance < closest:
                    peer = n
                    closest = distance

        echo "Found ", lookup.len, " nodes"

when isMainModule:
    waitFor run()
