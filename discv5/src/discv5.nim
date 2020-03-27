import
  random, chronos, sequtils, chronicles, tables, stint, options, std/bitops,
  eth/[keys, rlp, async_utils], eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types, routing_table, encoding],
  eth/p2p/discoveryv5/protocol as discv5_protocol,
  ./utils

const
    N = 100
    MAX_LOOKUPS = 10
    RUNS = 10

type
    NodeArray = array[N, discv5_protocol.Protocol]

proc randNode(nodes: NodeArray): Node =
    randomize()
    result = nodes[rand(N - 1)].localNode

proc runWith(node: discv5_protocol.Protocol, nodes: NodeArray) {.async.} =
    let target = randNode(nodes)
    let tid = recordToNodeID(target.record)

    var peer = randNode(nodes)
    var distance = distanceTo(recordToNodeID(peer.record), tid)
    var iterations = 0

    var called = newSeq[string](0)

    block outer:
        for i in 0..<MAX_LOOKUPS:
            let lookup = await node.findNode(peer, distance)
            called.add(peer.record.toUri())

            for n in items(lookup):
                let uri = n.record.toUri()
                if uri == target.record.toUri():
                    echo "Found target in ", iterations, " lookups"
                    break outer

                if containsNodeId(called, uri):
                    break

                let d = distanceTo(recordToNodeID(n.record), tid)
                if d <= distance:
                    peer = n
                    distance = d

    echo "Not found in max iterations"

proc run() {.async.} =
    var nodes: NodeArray

    for i in 0..<N:
        let node = initDiscoveryNode(newPrivateKey(), localAddress(20300 + i), if i > 0: @[nodes[0].localNode.record] else: @[])
        node.start()
        nodes[i] = node

    echo "Setup ", N, " nodes"

    echo "Sleeping for 50 seconds"
    await sleepAsync(50.seconds)

    let node = initDiscoveryNode(newPrivateKey(), localAddress(20300 + N), @[nodes[0].localNode.record])

    for i in 0..<RUNS:
        await runWith(node, nodes)
        await sleepAsync(5.seconds)

when isMainModule:
    waitFor run()
