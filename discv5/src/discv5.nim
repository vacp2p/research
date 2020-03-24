import
  random, chronos, sequtils, chronicles, tables, stint, options,
  eth/[keys, rlp, async_utils], eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types, routing_table, encoding],
  eth/p2p/discoveryv5/protocol as discv5_protocol,
  ./utils

proc run() {.async.} =
    let mainNode = initDiscoveryNode(newPrivateKey(), localAddress(20301), @[])
    for i in 0..<1000:
        mainNode.addNode(generateNode())

    let node = generateNode()

    let test = await mainNode.lookup(node.id)
    debug "Found nodes", len = test.len

when isMainModule:
    waitFor run()
