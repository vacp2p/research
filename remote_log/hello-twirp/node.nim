import os
import strformat
import strutils

import cas_service_pb
import cas_service_twirp

import ns_service_pb
import ns_service_twirp

import strutils
import byteutils

# CAS
var content = newvac_cas_Content()
try:
  content.data = hexToSeqByte("foo".toHex())
except:
  echo("Unable to create Content data")
  quit(QuitFailure)

let casClient = newCASClient("http://localhost:8001")

# XXX: resp is wrong here
try:
  let resp = Add(casClient, content)
  let str = parseHexStr(toHex(resp.id))
  echo(&"I got a new post: {str}")
except Exception as e:
  echo(&"Exception: {e.msg}")

# NS
var req = newvac_ns_NameUpdate()
try:
  req.name = "foo.com"
  req.content = hexToSeqByte("foo ns entry".toHex())
except:
  echo("Unable to create NameUpdate req")
  quit(QuitFailure)

# XXX
let nsClient = newNSClient("http://localhost:8002")

# XXX: resp is wrong here
try:
  let resp = Update(nsClient, req)
  let str = parseHexStr(toHex(resp.data))
  echo(&"I got a new post: {str}")
except Exception as e:
  echo(&"Exception: {e.msg}")


echo("Done")
