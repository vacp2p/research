import asyncdispatch
import asynchttpserver
import httpclient
import json
import strutils

import ns_service_pb

import nimtwirp/nimtwirp
import nimtwirp/errors

const
    NSPrefix* = "/twirp/vac.ns.NS/"

type
    NS* = ref NSObj
    NSObj* = object of RootObj
        UpdateImpl*: proc (service: NS, param: vac_ns_NameUpdate): Future[vac_ns_Response] {.gcsafe, closure.}
        FetchImpl*: proc (service: NS, param: vac_ns_Query): Future[vac_ns_Content] {.gcsafe, closure.}

proc Update*(service: NS, param: vac_ns_NameUpdate): Future[vac_ns_Response] {.async.} =
    if service.UpdateImpl == nil:
        raise newTwirpError(TwirpUnimplemented, "Update is not implemented")
    result = await service.UpdateImpl(service, param)

proc Fetch*(service: NS, param: vac_ns_Query): Future[vac_ns_Content] {.async.} =
    if service.FetchImpl == nil:
        raise newTwirpError(TwirpUnimplemented, "Fetch is not implemented")
    result = await service.FetchImpl(service, param)

proc newNS*(): NS =
    new(result)

proc handleRequest*(service: NS, req: Request): Future[nimtwirp.Response] {.async.} =
    let (contentType, methodName) = validateRequest(req, NSPrefix)

    if methodName == "Update":
        var inputMsg: vac_ns_NameUpdate

        if contentType == "application/protobuf":
            inputMsg = newvac_ns_NameUpdate(req.body)
        elif contentType == "application/json":
            let node = parseJson(req.body)
            inputMsg = parsevac_ns_NameUpdate(node)

        let outputMsg = await Update(service, inputMsg)

        if contentType == "application/protobuf":
            return nimtwirp.newResponse(serialize(outputMsg))
        elif contentType == "application/json":
            return nimtwirp.newResponse(toJson(outputMsg))
    elif methodName == "Fetch":
        var inputMsg: vac_ns_Query

        if contentType == "application/protobuf":
            inputMsg = newvac_ns_Query(req.body)
        elif contentType == "application/json":
            let node = parseJson(req.body)
            inputMsg = parsevac_ns_Query(node)

        let outputMsg = await Fetch(service, inputMsg)

        if contentType == "application/protobuf":
            return nimtwirp.newResponse(serialize(outputMsg))
        elif contentType == "application/json":
            return nimtwirp.newResponse(toJson(outputMsg))
    else:
        raise newTwirpError(TwirpBadRoute, "unknown method")


type
    NSClient* = ref object of nimtwirp.Client

proc newNSClient*(address: string, kind = ClientKind.Protobuf): NSClient =
    new(result)
    result.client = newHttpClient()
    result.kind = kind
    case kind
    of ClientKind.Protobuf:
        result.client.headers = newHttpHeaders({"Content-Type": "application/protobuf"})
    of ClientKind.Json:
        result.client.headers = newHttpHeaders({"Content-Type": "application/json"})
    result.address = address

proc Update*(client: NSClient, req: vac_ns_NameUpdate): vac_ns_Response =
    var body: string
    case client.kind
    of ClientKind.Protobuf:
        body = serialize(req)
    of ClientKind.Json:
        body = $toJson(req)
    let resp = request(client, NSPrefix, "Update", body)
    case client.kind
    of ClientKind.Protobuf:
        result = newvac_ns_Response(resp.body)
    of ClientKind.Json:
        result = parsevac_ns_Response(parseJson(resp.body))

proc Fetch*(client: NSClient, req: vac_ns_Query): vac_ns_Content =
    var body: string
    case client.kind
    of ClientKind.Protobuf:
        body = serialize(req)
    of ClientKind.Json:
        body = $toJson(req)
    let resp = request(client, NSPrefix, "Fetch", body)
    case client.kind
    of ClientKind.Protobuf:
        result = newvac_ns_Content(resp.body)
    of ClientKind.Json:
        result = parsevac_ns_Content(parseJson(resp.body))

