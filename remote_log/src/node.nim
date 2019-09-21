import os
import strformat
import strutils

import cas_service_pb
import cas_service_twirp

import ns_service_pb
import ns_service_twirp

import remote_log_pb
#import remote_log_twirp

import strutils
import byteutils

# CAS util
proc createContent*(s: string): vac_cas_Content =
  var content = newvac_cas_Content()
  try:
    content.data = hexToSeqByte(s.toHex())
  except:
    echo("Unable to create Content data")
    quit(QuitFailure)
  return content

let casClient = newCASClient("http://localhost:8001")

# XXX: resp is wrong here
try:
  let content = createContent("foo")
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

# TODO: Do the CAS and NS dance

# TODO: Remote log protobuf spec

# Remote log misc notes
# One one extreme just a linked list
# [[h1,h2], next]
# On other, fully fledged log (backup?)
# [[h1, data], [h2,..], nil]
# dealing with changing log loc
# guarantees and relaxation (should vs may data around)
# find out what data is missing
# privacy protection? wire assumption ~
# pack format

# Let's construct one here, example
var pairs: seq[vac_remotelog_RemoteLog_Pair]
var pair = newvac_remotelog_RemoteLog_Pair()
var body = newvac_remotelog_RemoteLog_Body()
var remotelog = newvac_remotelog_RemoteLog()
try:
  pair.remoteHash = hexToSeqByte("foo".toHex())
  pair.localHash = hexToSeqByte("foo2".toHex())
  body.pair = pairs
  remotelog.body = body
  remotelog.tail = hexToSeqByte("0x")
except:
  echo("Unable to create Remote log data")
  quit(QuitFailure)
