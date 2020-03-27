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

    block outer:
        while true:
            if iterations > MAX_LOOKUPS:
                echo "Couldn't find node in max iterations"
                break

            iterations = iterations + 1
            let lookup = await node.findNode(peer, distance)
            # echo "Found ", lookup.len, " nodes"

            var closest = 256
            for n in items(lookup):
                if n.record.toUri() == target.record.toUri():
                    echo "Found ", target.record.toUri(), " in ", iterations, " lookups"
                    break outer

                let d = distanceTo(recordToNodeID(n.record), tid)
                if d <= distance:
                    # echo "Distance ", d
                    peer = n
                    distance = d

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
        waitFor runWith(node, nodes)


when isMainModule:
    waitFor run()
