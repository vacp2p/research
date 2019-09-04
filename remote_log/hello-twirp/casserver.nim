import asynchttpserver
import asyncdispatch
import random

import nimtwirp/nimtwirp
import nimtwirp/errors

import cas_service_pb
import cas_service_twirp

import strutils
import byteutils

proc AddImpl(service: CAS, Address: vac_cas_Content): Future[vac_cas_Address] {.async.} =
  # TODO: Actually store this in a (non-persisted) hash table
  result = newvac_cas_Address()
  result.id = hexToSeqByte("id2".toHex())

# seq[bytes]

proc GetImpl(service: CAS, CASRequest: vac_cas_Address): Future[vac_cas_Content] {.async.} =
  result = newvac_cas_Content()
  result.data = hexToSeqByte("data2".toHex())

var
  server = newAsyncHttpServer()
  service {.threadvar.}: CAS

service = newCAS()
service.AddImpl = AddImpl

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
