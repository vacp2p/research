import
  random, chronos, sequtils, chronicles, tables, stint, options,
  eth/[keys, rlp], eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types, routing_table, encoding],
  eth/p2p/discoveryv5/protocol as discv5_protocol,
  ./utils

when isMainModule:
    let mainNode = initDiscoveryNode(newPrivateKey(), localAddress(20301), @[])

    for i in 0..<1000:
        mainNode.addNode(generateNode())

    runForever()