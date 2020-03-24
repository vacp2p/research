import
  confutils/defs, chronicles, chronos,
  eth/keys

type
  DiscConf* = object
    isBootnode* {.
      desc: "Start a bootnode."
      defaultValue: false
      name: "bootnode" }: bool
    bootstrap* {.
      desc: "ENode URL of a bootnode."
      defaultValue: ""
      name: "bootstrap" }: string

proc parseCmdArg*(T: type KeyPair, p: TaintedString): T =
  try:
    # TODO: add isValidPrivateKey check from Nimbus?
    result.seckey = initPrivateKey(p)
    result.pubkey = result.seckey.getPublicKey()
  except CatchableError as e:
    raise newException(ConfigurationError, "Invalid private key")

proc completeCmdArg*(T: type KeyPair, val: TaintedString): seq[string] =
  return @[]

proc parseCmdArg*(T: type IpAddress, p: TaintedString): T =
  try:
    result = parseIpAddress(p)
  except CatchableError as e:
    raise newException(ConfigurationError, "Invalid IP address")

proc completeCmdArg*(T: type IpAddress, val: TaintedString): seq[string] =
  return @[]