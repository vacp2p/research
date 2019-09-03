import asyncdispatch
import asynchttpserver
import httpclient
import json
import strutils

import protocol_pb

import nimtwirp/nimtwirp
import nimtwirp/errors

const
    CASPrefix* = "/twirp/vac.cas.CAS/"

type
    CAS* = ref CASObj
    CASObj* = object of RootObj
        GetImpl*: proc (service: CAS, param: vac_cas_CASRequest): Future[vac_cas_CASResponse] {.gcsafe, closure.}
        PostImpl*: proc (service: CAS, param: vac_cas_CASRequest): Future[vac_cas_CASResponse] {.gcsafe, closure.}

proc Get*(service: CAS, param: vac_cas_CASRequest): Future[vac_cas_CASResponse] {.async.} =
    if service.GetImpl == nil:
        raise newTwirpError(TwirpUnimplemented, "Get is not implemented")
    result = await service.GetImpl(service, param)

proc Post*(service: CAS, param: vac_cas_CASRequest): Future[vac_cas_CASResponse] {.async.} =
    if service.PostImpl == nil:
        raise newTwirpError(TwirpUnimplemented, "Post is not implemented")
    result = await service.PostImpl(service, param)

proc newCAS*(): CAS =
    new(result)

proc handleRequest*(service: CAS, req: Request): Future[nimtwirp.Response] {.async.} =
    let (contentType, methodName) = validateRequest(req, CASPrefix)

    if methodName == "Get":
        var inputMsg: vac_cas_CASRequest

        if contentType == "application/protobuf":
            inputMsg = newvac_cas_CASRequest(req.body)
        elif contentType == "application/json":
            let node = parseJson(req.body)
            inputMsg = parsevac_cas_CASRequest(node)

        let outputMsg = await Get(service, inputMsg)

        if contentType == "application/protobuf":
            return nimtwirp.newResponse(serialize(outputMsg))
        elif contentType == "application/json":
            return nimtwirp.newResponse(toJson(outputMsg))
    elif methodName == "Post":
        var inputMsg: vac_cas_CASRequest

        if contentType == "application/protobuf":
            inputMsg = newvac_cas_CASRequest(req.body)
        elif contentType == "application/json":
            let node = parseJson(req.body)
            inputMsg = parsevac_cas_CASRequest(node)

        let outputMsg = await Post(service, inputMsg)

        if contentType == "application/protobuf":
            return nimtwirp.newResponse(serialize(outputMsg))
        elif contentType == "application/json":
            return nimtwirp.newResponse(toJson(outputMsg))
    else:
        raise newTwirpError(TwirpBadRoute, "unknown method")


type
    CASClient* = ref object of nimtwirp.Client

proc newCASClient*(address: string, kind = ClientKind.Protobuf): CASClient =
    new(result)
    result.client = newHttpClient()
    result.kind = kind
    case kind
    of ClientKind.Protobuf:
        result.client.headers = newHttpHeaders({"Content-Type": "application/protobuf"})
    of ClientKind.Json:
        result.client.headers = newHttpHeaders({"Content-Type": "application/json"})
    result.address = address

proc Get*(client: CASClient, req: vac_cas_CASRequest): vac_cas_CASResponse =
    var body: string
    case client.kind
    of ClientKind.Protobuf:
        body = serialize(req)
    of ClientKind.Json:
        body = $toJson(req)
    let resp = request(client, CASPrefix, "Get", body)
    case client.kind
    of ClientKind.Protobuf:
        result = newvac_cas_CASResponse(resp.body)
    of ClientKind.Json:
        result = parsevac_cas_CASResponse(parseJson(resp.body))

proc Post*(client: CASClient, req: vac_cas_CASRequest): vac_cas_CASResponse =
    var body: string
    case client.kind
    of ClientKind.Protobuf:
        body = serialize(req)
    of ClientKind.Json:
        body = $toJson(req)
    let resp = request(client, CASPrefix, "Post", body)
    case client.kind
    of ClientKind.Protobuf:
        result = newvac_cas_CASResponse(resp.body)
    of ClientKind.Json:
        result = parsevac_cas_CASResponse(parseJson(resp.body))

