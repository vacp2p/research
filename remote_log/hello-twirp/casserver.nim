import asynchttpserver
import asyncdispatch
import random

import nimtwirp/nimtwirp
import nimtwirp/errors

import cas_service_pb
import cas_service_twirp

proc PostImpl(service: CAS, CASRequest: vac_cas_CASrequest): Future[vac_cas_CASResponse] {.async.} =
  result = newvac_cas_CASResponse()
  result.id = "foo2"
  result.data = "bar2"

# NYI: GetImpl


var
  server = newAsyncHttpServer()
  service {.threadvar.}: CAS

service = newCAS()
service.PostImpl = PostImpl

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
