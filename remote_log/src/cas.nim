import net, os, nativesockets, strutils, std/sha1, tables

type
  Message = object
    arg: string
    data: string

  ResponseCode = enum
    OK, ERROR

  # XXX: Want to have Response be either OkResp or ErrResp
  Response = object
    code: ResponseCode
    data: string

var server: Socket  = newSocket()

proc handler() {.noconv.} =
  stdout.write("Shutting down server.")

  # Unclear if this matters with ReuseAddr
  server.close()

  quit 0

setControlCHook(handler)

server.setSockOpt(OptReuseAddr, true)
server.getFd().setBlocking(false)
server.bindAddr(Port(6002))
server.listen()

# TODO: Implicit for Alice, can be part of startup args or so
stdout.writeLine("Content addressable storage starting, listening on 6002")

var clients: seq[Socket] = @[]

#assert("POST :foo bar".split(':')[1] == "foo bar"

# XXX: Single global mutating state, fish memory
var contentStorage = initTable[string,string]()

proc contentHash(data: string): string =
  # Prepend constant to highlight fact that hash fns can be different
  let str = "storage-" & data
  let sha1 = secureHash(str)
  return $sha1

proc parseMessage(message: string): Message =
  var msg = Message()
  stdout.writeLine("Server: received from client: ", message)
  try:
    msg.arg = message.split(' ')[0]
    msg.data = message.split(':')[1]
  except:
    echo("Unable to parse message: ", message)

  return msg

proc store(data: string): string =
  let hash = contentHash(data)
  echo("store: ", hash)
  contentStorage[hash] = data
  echo("store content: ", $contentStorage)
  return hash

proc handleMessage(message: Message): Response =
  let arg = message.arg
  let data = message.data

  if arg == "POST":
    echo("posting: ", data)
    let key = store(data)
    # XXX: Ad hoc protocol
    let ret = data & " " & key
    echo "Returning from post: ", ret
    return Response(code: OK, data: ret)

  elif arg == "GET":
    echo("getting: ", data)
    # XXX: No validation etc, nil?
    let data = contentStorage[data]
    return Response(code: OK, data: data)

  else:
    echo("Unable to handle message: ", message)
    return Response(code: ERROR, data: "bad message")

while true:
  try:
    var client: Socket = new(Socket)
    server.accept(client)
    clients.add(client)
    stdout.writeLine("Server: client connected")
  except OSError:
    discard

  var clientsToRemove: seq[int] = @[]
  for index, client in clients:
    try:
      let message: string = client.recvLine(timeout = 1)

      if message == "":
        clientsToRemove.add(index)

      let resp = handleMessage(parseMessage(message))
      # TODO: Respond to client
      # XXX: Client is currently non-interactive so sending to other client
      # That is, node is split into node_receiving and node_sending
      # Sending to all clients:
      echo("RESPONSE: ", resp)
      for c in clients:
        c.send(resp.data & "\r\L")

    except TimeoutError:
      discard

  for index in clientsToRemove:
    clients.del(index)
    stdout.writeLine("Server: client disconnected")

server.close()
