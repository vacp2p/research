import
  random, chronos, sequtils, chronicles, tables, stint, options, std/bitops, sequtils,
  eth/[keys, rlp, async_utils], eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types, routing_table, encoding],
  eth/p2p/discoveryv5/protocol as discv5_protocol,
  ./utils

const
    # the amount of nodes
    N = 100

    MAX_LOOKUPS = 100
    RUNS = 100

    # the cooldown period between runs.
    COOLDOWN = 0

    # the sleep period before starting our runs.
    SLEEP = 600
    VERBOSE = true

    # if true, nodes are randomly added to other nodes using the `addNode` function.
    # otherwise we use discv5s native paring functionality letting each node find peers using the boostrap.
    USE_MANUAL_PAIRING = false

    # when manual pairing is enabled this indicates the amount of nodes to pair with.
    PEERS_PER_NODE = 16

    # True if looking for a node with field rather than a specific node
    LOOK_FOR_FIELD = true

    # The amount of nodes that will have our specific field to look for
    LOOKUP_FIELD_DISTRIBUTION = 5

proc write(str: string) =
    if VERBOSE:
        echo str

proc runWith(node: discv5_protocol.Protocol, nodes: seq[discv5_protocol.Protocol]) {.async.} =
    randomize()

    let target = sample(nodes).localNode
    let tid = recordToNodeID(target.record)

    var peer: Node
    while true:
        randomize()
        peer = sample(nodes).localNode
        if peer.record.toUri() != target.record.toUri():
            break

    var distance = logDist(recordToNodeID(peer.record), tid)

    var called = newSeq[string](0)

    for i in 0..<MAX_LOOKUPS:
        var lookup = await node.findNode(peer, distance)
        called.add(peer.record.toUri())

        keepIf(lookup, proc (x: Node): bool =
            x.record.toUri() != node.localNode.record.toUri() and not called.contains(x.record.toUri())
        )

        if lookup.len == 0:
            if distance != 256:
                distance = 256
                continue

            write("Lookup from node " & $((get peer.record.toTypedRecord()).udp.get()) & " found no results at 256")
            return

        if count(lookup, proc (x: Node): bool = x.record.toUri() == target.record.toUri()) == 1:
            echo i + 1
            return

        let lastPeer = peer
        for n in items(lookup):
            let d = logDist(recordToNodeID(n.record), tid)
            if d <= distance:
                peer = n
                distance = d

        # This ensures we get a random node from the last lookup if we have already called the new peer.
        # We let this run lookup*2 times, otherwise we could reach deadlock.
        for i in 0..<(lookup.len*2):
            if lastPeer.record.toUri() != peer.record.toUri():
                break

            peer = sample(lookup)

    echo "Not found in max iterations"

proc runWithENR(node: discv5_protocol.Protocol, nodes: seq[discv5_protocol.Protocol]) {.async.} =
    randomize()

    var peer = sample(nodes).localNode

    let distance = uint32(256)

    var called = newSeq[string](0)

    for i in 0..<MAX_LOOKUPS:
        var lookup = await node.findNode(peer, distance)
        called.add(peer.record.toUri())

        keepIf(lookup, proc (x: Node): bool =
            x.record.toUri() != node.localNode.record.toUri() and not called.contains(x.record.toUri())
        )

        for x in lookup:
            if x.record.tryGet("search", uint).isSome:
                echo i + 1
                return

        if lookup.len == 0:
            write("Lookup from node " & $((get peer.record.toTypedRecord()).udp.get()) & " found no results at 256")
            return

        peer = sample(lookup)

    echo "Not found in max iterations"

proc runWithRandom(node: discv5_protocol.Protocol, nodes: seq[discv5_protocol.Protocol]) {.async.} =
    randomize()

    let target = sample(nodes).localNode
    let tid = recordToNodeID(target.record)

    var peer: Node
    while true:
        randomize()
        peer = sample(nodes).localNode
        if peer.record.toUri() != target.record.toUri():
            break

    var called = newSeq[string](0)

    for i in 0..<MAX_LOOKUPS:
        var lookup = await node.findNode(peer, 256)
        called.add(peer.record.toUri())

        keepIf(lookup, proc (x: Node): bool =
            x.record.toUri() != node.localNode.record.toUri() and not called.contains(x.record.toUri())
        )

        if lookup.len == 0:
            write("Lookup from node " & $((get peer.record.toTypedRecord()).udp.get()) & " found no results at 256")
            return

        let findings = filter(lookup, proc (x: Node): bool =
            x.record.toUri() == target.record.toUri()
        )

        if findings.len == 1:
            echo "Found target in ", i + 1, " lookups"
            return

        while true: # This ensures we get a random node from the last lookup if we have already called the new peer.
            if not called.contains(peer.record.toUri()):
                break

            peer = sample(lookup)

    echo "Not found in max iterations"

proc pair(node: discv5_protocol.Protocol, nodes: seq[discv5_protocol.Protocol]) =
    for _ in 0..<PEERS_PER_NODE:
        randomize()
        sample(nodes).addNode(node.localNode)

proc run() {.async.} =
    var nodes = newSeq[discv5_protocol.Protocol](0)

    echo "Setting up ", N, " nodes"

    let divisor = int(N / LOOKUP_FIELD_DISTRIBUTION)

    for i in 0..<N:
        let node = initDiscoveryNode(
            PrivateKey.random().get,
            localAddress(20300 + i),
            if i > 0: @[nodes[0].localNode.record] else: @[],
            if i mod divisor == 0: 1 else: 0
        )
        nodes.add(node)

        if (USE_MANUAL_PAIRING and i == 0) or not USE_MANUAL_PAIRING:
            node.start()

    if USE_MANUAL_PAIRING:
        for n in nodes:
            pair(n, nodes)

    if not USE_MANUAL_PAIRING:
        echo "Sleeping for ", SLEEP, " seconds"
        await sleepAsync(SLEEP.seconds)

    let node = initDiscoveryNode(PrivateKey.random().get, localAddress(20300 + N), @[nodes[0].localNode.record], 0)

    for i in 0..<RUNS:
        if LOOK_FOR_FIELD:
               await runWithENR(node, nodes)
        else:
           await runWith(node, nodes)

        await sleepAsync(COOLDOWN.seconds)

when isMainModule:
    waitFor run()
