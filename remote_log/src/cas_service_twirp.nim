import asyncdispatch
import asynchttpserver
import httpclient
import json
import strutils

import cas_service_pb

import nimtwirp/nimtwirp
import nimtwirp/errors

const
    CASPrefix* = "/twirp/vac.cas.CAS/"

type
    CAS* = ref CASObj
    CASObj* = object of RootObj
        AddImpl*: proc (service: CAS, param: vac_cas_Content): Future[vac_cas_Address] {.gcsafe, closure.}
        GetImpl*: proc (service: CAS, param: vac_cas_Address): Future[vac_cas_Content] {.gcsafe, closure.}

proc Add*(service: CAS, param: vac_cas_Content): Future[vac_cas_Address] {.async.} =
    if service.AddImpl == nil:
        raise newTwirpError(TwirpUnimplemented, "Add is not implemented")
    result = await service.AddImpl(service, param)

proc Get*(service: CAS, param: vac_cas_Address): Future[vac_cas_Content] {.async.} =
    if service.GetImpl == nil:
        raise newTwirpError(TwirpUnimplemented, "Get is not implemented")
    result = await service.GetImpl(service, param)

proc newCAS*(): CAS =
    new(result)

proc handleRequest*(service: CAS, req: Request): Future[nimtwirp.Response] {.async.} =
    let (contentType, methodName) = validateRequest(req, CASPrefix)

    if methodName == "Add":
        var inputMsg: vac_cas_Content

        if contentType == "application/protobuf":
            inputMsg = newvac_cas_Content(req.body)
        elif contentType == "application/json":
            let node = parseJson(req.body)
            inputMsg = parsevac_cas_Content(node)

        let outputMsg = await Add(service, inputMsg)

        if contentType == "application/protobuf":
            return nimtwirp.newResponse(serialize(outputMsg))
        elif contentType == "application/json":
            return nimtwirp.newResponse(toJson(outputMsg))
    elif methodName == "Get":
        var inputMsg: vac_cas_Address

        if contentType == "application/protobuf":
            inputMsg = newvac_cas_Address(req.body)
        elif contentType == "application/json":
            let node = parseJson(req.body)
            inputMsg = parsevac_cas_Address(node)

        let outputMsg = await Get(service, inputMsg)

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

proc Add*(client: CASClient, req: vac_cas_Content): vac_cas_Address =
    var body: string
    case client.kind
    of ClientKind.Protobuf:
        body = serialize(req)
    of ClientKind.Json:
        body = $toJson(req)
    let resp = request(client, CASPrefix, "Add", body)
    case client.kind
    of ClientKind.Protobuf:
        result = newvac_cas_Address(resp.body)
    of ClientKind.Json:
        result = parsevac_cas_Address(parseJson(resp.body))

proc Get*(client: CASClient, req: vac_cas_Address): vac_cas_Content =
    var body: string
    case client.kind
    of ClientKind.Protobuf:
        body = serialize(req)
    of ClientKind.Json:
        body = $toJson(req)
    let resp = request(client, CASPrefix, "Get", body)
    case client.kind
    of ClientKind.Protobuf:
        result = newvac_cas_Content(resp.body)
    of ClientKind.Json:
        result = parsevac_cas_Content(parseJson(resp.body))

