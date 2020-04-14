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
    result = newProtocol(privKey, db, some(parseIpAddress("127.0.0.1")), address.tcpPort, address.udpPort, bootstrapRecords)
    result.open()

proc count*[T](s: openArray[T], pred: proc(x: T): bool {.closure.}): int
                                                                  {.inline.} =
    ## Returns a count of all the items that fulfilled the predicate.
    ##
    ## Example:
    ##
    ## .. code-block::
    ##   let
    ##     numbers = @[1, 2, 3]
    ##     f1 = count(numbers, proc(x: int): bool = x < 3)
    ##     f2 = count(numbers) do (x: int) -> bool : x >= 2
    ##   assert f1 == 2
    ##   assert f2 == 2
    result = 0
    for i in 0 ..< s.len:
        if pred(s[i]):
            result += 1

proc recordToNodeID*(r: Record): NodeId =
    var pk = r.get(PublicKey)
    result = readUintBE[256](keccak256.digest(pk.get.toRaw()).data)
