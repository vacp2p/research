import
  random, chronos, sequtils, chronicles, tables, stint, options, std/bitops,
  eth/[keys, rlp, async_utils], eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types, routing_table, encoding],
  eth/p2p/discoveryv5/protocol as discv5_protocol,
  ./utils

const
    N = 64
    MAX_LOOKUPS = 10
    RUNS = 10
    SLEEP = 50

proc runWith(node: discv5_protocol.Protocol, nodes: seq[discv5_protocol.Protocol]) {.async.} =
    randomize()

    let target = sample(nodes).localNode
    let tid = recordToNodeID(target.record)

    var peer: Node
    while true:
        peer = sample(nodes).localNode
        if peer.record.toUri() != target.record.toUri():
            break

    var distance = logDist(recordToNodeID(peer.record), tid)

    var called = newSeq[string](0)

    for i in 0..<MAX_LOOKUPS:
        let lookup = await node.findNode(peer, distance)
        called.add(peer.record.toUri())

        if lookup.len == 0:
            distance = 256
            continue

        for n in items(lookup):
            let uri = n.record.toUri()
            if uri == target.record.toUri():
                echo "Found target in ", i + 1, " lookups"
                return

            if called.contains(uri):
                continue

            let d = logDist(recordToNodeID(n.record), tid)
            if d < distance:
                peer = n
                distance = d

        while true: # This ensures we get a random node from the last lookup if we have already called the new peer.
            if not called.contains(peer.record.toUri()):
                break

            peer = sample(lookup)

    echo "Not found in max iterations"

proc run() {.async.} =
    var nodes = newSeq[discv5_protocol.Protocol](0)

    for i in 0..<N:
        let node = initDiscoveryNode(newPrivateKey(), localAddress(20300 + i), if i > 0: @[nodes[0].localNode.record] else: @[])
        nodes.add(node)

    echo "Setup ", N, " nodes"

    echo "Sleeping for ", SLEEP, " seconds"
    await sleepAsync(SLEEP.seconds)

    let node = initDiscoveryNode(newPrivateKey(), localAddress(20300 + N), @[nodes[0].localNode.record])

    for i in 0..<RUNS:
        await runWith(node, nodes)
        await sleepAsync(5.seconds)

when isMainModule:
    waitFor run()
