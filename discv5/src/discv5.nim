import
  random, chronos, sequtils, chronicles, tables, stint, options,
  eth/[keys, rlp], eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types, routing_table, encoding],
  eth/p2p/discoveryv5/protocol as discv5_protocol,
  ./utils

proc run() =
    let mainNode = initDiscoveryNode(newPrivateKey(), localAddress(20301), @[])

    let peer = initDiscoveryNode(newPrivateKey(), localAddress(20302), @[mainNode.localNode.record])

    runForever()

when isMainModule:
    run()
