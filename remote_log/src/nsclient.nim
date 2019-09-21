import os
import strformat
import strutils

import ns_service_pb
import ns_service_twirp

import strutils
import byteutils

var req = newvac_ns_NameUpdate()
try:
  req.name = "foo.com"
  req.content = hexToSeqByte("foo ns entry".toHex())
except:
  echo("Unable to create NameUpdate req")
  quit(QuitFailure)

# XXX
let client = newNSClient("http://localhost:8002")

# XXX: resp is wrong here
try:
  let resp = Update(client, req)
  let str = parseHexStr(toHex(resp.data))
  echo(&"I got a new post: {str}")
except Exception as e:
  echo(&"Exception: {e.msg}")

# TODO: IPFS IPNS as NS
# TODO: Swarm Feeds as NS
