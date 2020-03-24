import
  chronos, options,
  eth/keys, eth/p2p/enode, eth/trie/db,
  eth/p2p/discoveryv5/[discovery_db, enr, node],
  eth/p2p/discoveryv5/protocol as discv5_protocol

proc localAddress*(port: int): Address =
    let port = Port(port)
    result = Address(
        udpPort: port,
        tcpPort: port,
        ip: parseIpAddress("127.0.0.1")
    )

proc initDiscoveryNode*(privKey: PrivateKey, address: Address,bootstrapRecords: seq[Record]): discv5_protocol.Protocol =
    var db = DiscoveryDB.init(newMemoryDB())
    result = newProtocol(privKey, db, parseIpAddress("127.0.0.1"), address.tcpPort, address.udpPort, bootstrapRecords)
    result.open()

proc generateNode*(privKey = newPrivateKey()): Node =
    let enr = enr.Record.init(1, privKey, none(Address))
    result = newNode(enr)
