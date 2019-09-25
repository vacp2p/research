import asynchttpserver
import asyncdispatch
import random

import nimtwirp/nimtwirp
import nimtwirp/errors

import cas_service_pb
import cas_service_twirp

import strutils
import byteutils
import std/sha1
import tables

# TODO: Rename casserver->cas, same with ns

# contentStorage maps addresses (encoded as strings) to content.
#
# XXX: Single global mutating state, fish memory
# TODO: Implement map as fixed-length byte sequence
var contentStorage = initTable[string,vac_cas_Content]()

proc contentHash(data: string): string =
  # Add constant to ensure hashes are different
  # This is likely the case in production environments
  let str = "storage-" & data
  let sha1 = toLowerAscii($secureHash(str))
  return sha1

# XXX: This procedure is not GC safe since it accesses global db
proc store(data: vac_cas_Content): string =
  var s = serialize(data)
  echo("Store serialized data: <", s, ">")
  let hash = contentHash(s)
  contentStorage[hash] = data

  # Print out whole cas db
  echo("contentStorage:")
  for k, v in contentStorage:
    echo("cas hash: <", k, "> cas content: <", serialize(v), ">")
  return hash

proc AddImpl(service: CAS, content: vac_cas_Content): Future[vac_cas_Address] {.gcsafe, async.} =
  let hash = store(content)
  result = newvac_cas_Address()
  result.id = hexToSeqByte(hash.toHex())

proc GetImpl(service: CAS, address: vac_cas_Address): Future[vac_cas_Content] {.gcsafe, async.} =
  # We use hexstring of the bytes id as hash index
  let hash = tohex(address.id)
  echo("GetImpl Address: <", hash, ">")
  # This doesnt work
  if contentStorage.hasKey(hash):
    let content = contentStorage[hash]
    echo("Content:", serialize(content))
    result = content
  else:
    echo("Key not found in content store: <", hash, ">")
    #XXX: wrong
    result = newvac_cas_Content()
  # NYI
  #result.data = hexToSeqByte("data3".toHex())

var
  server = newAsyncHttpServer()
  service {.threadvar.}: CAS

service = newCAS()
service.AddImpl = AddImpl
service.GetImpl = GetImpl

proc handler(req: Request) {.async.} =
  # Each service will have a generated handleRequest() proc which takes the
  # service object and a asynchttpserver.Request object and returns a
  # Future[nimtwirp.Response].
  var fut = handleRequest(service, req)
  yield fut
  if fut.failed:
    await respond(req, nimtwirp.newResponse(fut.readError()))
  else:
    await respond(req, fut.read())

waitFor server.serve(Port(8001), handler)
