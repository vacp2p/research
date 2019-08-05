import net, os, nativesockets, strutils

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
server.bindAddr(Port(6001))
server.listen()

# TODO: Implicit for Alice, can be part of startup args or so
stdout.writeLine("Name service starting, listening on 6001")

var clients: seq[Socket] = @[]

#assert("POST :foo bar".split(':')[1] == "foo bar"

# XXX: Single global mutating state, fish memory
# Could be a DB type and persist to disk
var currentName = ""

proc parseMessage(message: string): Message =
  var msg = Message()
  stdout.writeLine("Server: received from client: ", message)
  try:
    msg.arg = message.split(' ')[0]
    msg.data = message.split(':')[1]
  except:
    echo("Unable to parse message: ", message)

  return msg

proc handleMessage(message: Message): Response =
  let arg = message.arg
  let data = message.data

  if arg == "POST":
    echo("posting: ", data)
    currentName = data
    return Response(code: OK, data: currentName)

  elif arg == "GET":
    echo("getting: ", data)
    return Response(code: OK, data: currentName)

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
      echo("RESPONSE: ", resp)

    except TimeoutError:
      discard

  for index in clientsToRemove:
    clients.del(index)
    stdout.writeLine("Server: client disconnected")

server.close()
