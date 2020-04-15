import
  chronos, options, std/bitops,
  eth/keys, eth/p2p/enode, eth/trie/db, stint, nimcrypto,
  eth/p2p/discoveryv5/[discovery_db, enr, node, types],
  eth/p2p/discoveryv5/protocol as discv5_protocol

type ToNodeIDError* = object of CatchableError

proc localAddress*(port: int): Address =
    let port = Port(port)
    result = Address(
        udpPort: port,
        tcpPort: port,
        ip: parseIpAddress("127.0.0.1")
    )

proc initDiscoveryNode*(privKey: PrivateKey, address: Address, bootstrapRecords: seq[Record], field: uint): discv5_protocol.Protocol =
    var db = DiscoveryDB.init(newMemoryDB())
    result = newProtocol(privKey, db, some(parseIpAddress("127.0.0.1")), address.tcpPort, address.udpPort, bootstrapRecords)
    let old = result.localNode.record

    if field == 1:
        let enr = initRecord(
            old.seqNum,
            privKey,
            {
                "udp": uint32(address.udpPort),
                "tcp": uint32(address.tcpPort),
                "ip": [byte 127, 0, 0, 1],
                "search": field
             }
        )

        result.localNode.record = enr

    result.open()

proc recordToNodeID*(r: Record): NodeId =
    var pk = r.get(PublicKey)
    result = readUintBE[256](keccak256.digest(pk.get.toRaw()).data)
