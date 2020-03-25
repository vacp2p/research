import
  random, chronos, sequtils, chronicles, tables, stint, options,
  eth/[keys, rlp, async_utils], eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types, routing_table, encoding],
  eth/p2p/discoveryv5/protocol as discv5_protocol,
  ./utils

const N = 100

proc run() {.async.} =
    type
        NodeArray = array[N, discv5_protocol.Protocol]
    var
        nodes: NodeArray

    for i in 0..<N:
        let node = initDiscoveryNode(newPrivateKey(), localAddress(20300 + i), if i > 0: @[nodes[0].localNode.record] else: @[])
        node.start()
        nodes[i] = node
        # if i > 0:
        #    nodes[0].addNode(nodes[i].localNode.record)

    let node = generateNode()

    let test = await nodes[0].lookup(node.id)
    debug "Found nodes", len = test.len
    runForever()

when isMainModule:
    waitFor run()
