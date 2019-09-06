import asynchttpserver
import asyncdispatch
import random

import nimtwirp/nimtwirp
import nimtwirp/errors

import ns_service_pb
import ns_service_twirp

import strutils
import byteutils

proc UpdateImpl(service: NS, param: vac_ns_NameUpdate): Future[vac_ns_Response] {.async.} =
  # TODO: Actually store previous data
  result = newvac_ns_Response()
  result.data = hexToSeqByte("ok".toHex())

proc FetchImpl(service: NS, param: vac_ns_Query): Future[vac_ns_Content] {.async.} =
  # TODO: Actually fetch previous data
  result = newvac_ns_Content()
  result.data = hexToSeqByte("data2".toHex())

var
  server = newAsyncHttpServer()
  service {.threadvar.}: NS

service = newNS()
service.UpdateImpl = UpdateImpl
service.FetchImpl = FetchImpl

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

waitFor server.serve(Port(8002), handler)
