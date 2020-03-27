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

proc initDiscoveryNode*(privKey: PrivateKey, address: Address, bootstrapRecords: seq[Record]): discv5_protocol.Protocol =
    var db = DiscoveryDB.init(newMemoryDB())
    result = newProtocol(privKey, db, parseIpAddress("127.0.0.1"), address.tcpPort, address.udpPort, bootstrapRecords)
    result.open()

proc generateNode*(privKey = newPrivateKey()): Node =
    let enr = enr.Record.init(1, privKey, none(Address))
    result = newNode(enr)

proc recordToNodeID*(r: Record): NodeId =
    var pk: PublicKey
    if recoverPublicKey(r.get("secp256k1", seq[byte]), pk) != EthKeysStatus.Success:
        raise newException(ToNodeIDError, "rip")

    result = readUintBE[256](keccak256.digest(pk.getRaw()).data)

proc distanceTo*(a, b: NodeId): uint32 =
    let a = a.toBytes
    let b = b.toBytes
    var lz = 0
    for i in countdown(a.len - 1, 0):
        let x = a[i] xor b[i]
        if x == 0:
            lz += 8
        else:
            lz += bitops.countLeadingZeroBits(x)
            break
    return uint32(a.len * 8 - lz)