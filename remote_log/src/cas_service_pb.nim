# Generated by protoc_gen_nim. Do not edit!

import base64
import intsets
import json
import strutils

import nimpb/nimpb
import nimpb/json as nimpb_json

type
    vac_cas_Address* = ref vac_cas_AddressObj
    vac_cas_AddressObj* = object of Message
        id: seq[byte]
    vac_cas_Content* = ref vac_cas_ContentObj
    vac_cas_ContentObj* = object of Message
        data: seq[byte]

proc newvac_cas_Content*(): vac_cas_Content
proc newvac_cas_Content*(data: string): vac_cas_Content
proc newvac_cas_Content*(data: seq[byte]): vac_cas_Content
proc writevac_cas_Content*(stream: Stream, message: vac_cas_Content)
proc readvac_cas_Content*(stream: Stream): vac_cas_Content
proc sizeOfvac_cas_Content*(message: vac_cas_Content): uint64
proc toJson*(message: vac_cas_Content): JsonNode
proc parsevac_cas_Content*(obj: JsonNode): vac_cas_Content

proc newvac_cas_Address*(): vac_cas_Address
proc newvac_cas_Address*(data: string): vac_cas_Address
proc newvac_cas_Address*(data: seq[byte]): vac_cas_Address
proc writevac_cas_Address*(stream: Stream, message: vac_cas_Address)
proc readvac_cas_Address*(stream: Stream): vac_cas_Address
proc sizeOfvac_cas_Address*(message: vac_cas_Address): uint64
proc toJson*(message: vac_cas_Address): JsonNode
proc parsevac_cas_Address*(obj: JsonNode): vac_cas_Address

proc fullyQualifiedName*(T: typedesc[vac_cas_Content]): string = "vac.cas.Content"

proc readvac_cas_ContentImpl(stream: Stream): Message = readvac_cas_Content(stream)
proc writevac_cas_ContentImpl(stream: Stream, msg: Message) = writevac_cas_Content(stream, vac_cas_Content(msg))
proc toJsonvac_cas_ContentImpl(msg: Message): JsonNode = toJson(vac_cas_Content(msg))
proc fromJsonvac_cas_ContentImpl(node: JsonNode): Message = parsevac_cas_Content(node)

proc vac_cas_ContentProcs*(): MessageProcs =
    result.readImpl = readvac_cas_ContentImpl
    result.writeImpl = writevac_cas_ContentImpl
    result.toJsonImpl = toJsonvac_cas_ContentImpl
    result.fromJsonImpl = fromJsonvac_cas_ContentImpl

proc newvac_cas_Content*(): vac_cas_Content =
    new(result)
    initMessage(result[])
    result.procs = vac_cas_ContentProcs()
    result.data = @[]

proc cleardata*(message: vac_cas_Content) =
    message.data = @[]

proc setdata*(message: vac_cas_Content, value: seq[byte]) =
    message.data = value

proc data*(message: vac_cas_Content): seq[byte] {.inline.} =
    message.data

proc `data=`*(message: vac_cas_Content, value: seq[byte]) {.inline.} =
    setdata(message, value)

proc sizeOfvac_cas_Content*(message: vac_cas_Content): uint64 =
    if len(message.data) > 0:
        result = result + sizeOfTag(1, WireType.LengthDelimited)
        result = result + sizeOfBytes(message.data)
    result = result + sizeOfUnknownFields(message)

proc writevac_cas_Content*(stream: Stream, message: vac_cas_Content) =
    if len(message.data) > 0:
        protoWriteBytes(stream, message.data, 1)
    writeUnknownFields(stream, message)

proc readvac_cas_Content*(stream: Stream): vac_cas_Content =
    result = newvac_cas_Content()
    while not atEnd(stream):
        let
            tag = readTag(stream)
            wireType = wireType(tag)
        case fieldNumber(tag)
        of 0:
            raise newException(InvalidFieldNumberError, "Invalid field number: 0")
        of 1:
            expectWireType(wireType, WireType.LengthDelimited)
            setdata(result, protoReadBytes(stream))
        else: readUnknownField(stream, result, tag)

proc toJson*(message: vac_cas_Content): JsonNode =
    result = newJObject()
    if len(message.data) > 0:
        result["data"] = %message.data

proc parsevac_cas_Content*(obj: JsonNode): vac_cas_Content =
    result = newvac_cas_Content()
    var node: JsonNode
    if obj.kind != JObject:
        raise newException(nimpb_json.ParseError, "object expected")
    node = getJsonField(obj, "data", "data")
    if node != nil and node.kind != JNull:
        setdata(result, parseBytes(node))

proc serialize*(message: vac_cas_Content): string =
    let
        ss = newStringStream()
    writevac_cas_Content(ss, message)
    result = ss.data

proc newvac_cas_Content*(data: string): vac_cas_Content =
    let
        ss = newStringStream(data)
    result = readvac_cas_Content(ss)

proc newvac_cas_Content*(data: seq[byte]): vac_cas_Content =
    let
        ss = newStringStream(cast[string](data))
    result = readvac_cas_Content(ss)


proc fullyQualifiedName*(T: typedesc[vac_cas_Address]): string = "vac.cas.Address"

proc readvac_cas_AddressImpl(stream: Stream): Message = readvac_cas_Address(stream)
proc writevac_cas_AddressImpl(stream: Stream, msg: Message) = writevac_cas_Address(stream, vac_cas_Address(msg))
proc toJsonvac_cas_AddressImpl(msg: Message): JsonNode = toJson(vac_cas_Address(msg))
proc fromJsonvac_cas_AddressImpl(node: JsonNode): Message = parsevac_cas_Address(node)

proc vac_cas_AddressProcs*(): MessageProcs =
    result.readImpl = readvac_cas_AddressImpl
    result.writeImpl = writevac_cas_AddressImpl
    result.toJsonImpl = toJsonvac_cas_AddressImpl
    result.fromJsonImpl = fromJsonvac_cas_AddressImpl

proc newvac_cas_Address*(): vac_cas_Address =
    new(result)
    initMessage(result[])
    result.procs = vac_cas_AddressProcs()
    result.id = @[]

proc clearid*(message: vac_cas_Address) =
    message.id = @[]

proc setid*(message: vac_cas_Address, value: seq[byte]) =
    message.id = value

proc id*(message: vac_cas_Address): seq[byte] {.inline.} =
    message.id

proc `id=`*(message: vac_cas_Address, value: seq[byte]) {.inline.} =
    setid(message, value)

proc sizeOfvac_cas_Address*(message: vac_cas_Address): uint64 =
    if len(message.id) > 0:
        result = result + sizeOfTag(1, WireType.LengthDelimited)
        result = result + sizeOfBytes(message.id)
    result = result + sizeOfUnknownFields(message)

proc writevac_cas_Address*(stream: Stream, message: vac_cas_Address) =
    if len(message.id) > 0:
        protoWriteBytes(stream, message.id, 1)
    writeUnknownFields(stream, message)

proc readvac_cas_Address*(stream: Stream): vac_cas_Address =
    result = newvac_cas_Address()
    while not atEnd(stream):
        let
            tag = readTag(stream)
            wireType = wireType(tag)
        case fieldNumber(tag)
        of 0:
            raise newException(InvalidFieldNumberError, "Invalid field number: 0")
        of 1:
            expectWireType(wireType, WireType.LengthDelimited)
            setid(result, protoReadBytes(stream))
        else: readUnknownField(stream, result, tag)

proc toJson*(message: vac_cas_Address): JsonNode =
    result = newJObject()
    if len(message.id) > 0:
        result["id"] = %message.id

proc parsevac_cas_Address*(obj: JsonNode): vac_cas_Address =
    result = newvac_cas_Address()
    var node: JsonNode
    if obj.kind != JObject:
        raise newException(nimpb_json.ParseError, "object expected")
    node = getJsonField(obj, "id", "id")
    if node != nil and node.kind != JNull:
        setid(result, parseBytes(node))

proc serialize*(message: vac_cas_Address): string =
    let
        ss = newStringStream()
    writevac_cas_Address(ss, message)
    result = ss.data

proc newvac_cas_Address*(data: string): vac_cas_Address =
    let
        ss = newStringStream(data)
    result = readvac_cas_Address(ss)

proc newvac_cas_Address*(data: seq[byte]): vac_cas_Address =
    let
        ss = newStringStream(cast[string](data))
    result = readvac_cas_Address(ss)


