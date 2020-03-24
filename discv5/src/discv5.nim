import
  confutils, config, random, chronos, sequtils, chronicles, tables, stint, options,
  eth/[keys, rlp], eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types, routing_table, encoding],
  eth/p2p/discoveryv5/protocol as discv5_protocol,
  ./utils

proc bootnode() =
    let mainNode = initDiscoveryNode(newPrivateKey(), localAddress(20301), @[])

    echo mainNode.localNode.record.toURI()

    for i in 0..<1000:
        mainNode.addNode(generateNode())

proc client(config: DiscConf) =

    var r: Record
    assert(r.fromURI(config.bootstrap))

    let peer = initDiscoveryNode(newPrivateKey(), localAddress(20302), @[r])
    peer.start()

proc run(config: DiscConf) =
    if config.isBootnode:
        bootnode()
    else:
        client(config)

    runForever()

when isMainModule:
    let conf = DiscConf.load()
    run(conf)


