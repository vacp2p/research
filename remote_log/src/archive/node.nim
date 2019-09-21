import net, os, threadpool, asyncdispatch, asyncnet, strutils, streams
include protocol

var socket1 = newAsyncSocket()
var socket2 = newAsyncSocket()

proc handler() {.noconv.} =
  stdout.writeLine("Shutting down connection.")
  socket1.close()
  socket2.close()
  quit 0

setControlCHook(handler)

# TODO: Move to protocol yeah
proc parseCASResponse(msg: string): CASResponse =
  var stream = newStringStream()
  stream.write(msg)
  stream.setPosition(0)
  var readMsg = stream.readCASResponse()
  if readMsg is CASResponse:
    return readMsg
  # XXX: How to get actual type?
  else:
    raise newException(Exception, "Unable to parse data, not a CASResponse: " & msg)

# TODO: Shouldn't crash just cause other nodes not online
proc connect(socket: AsyncSocket, serverAddr: string, portInt: int) {.async.} =
  echo("Connecting to ", serverAddr, ":", portInt)
  await socket.connect(serverAddr, portInt.Port)
  echo(portInt, ": Connected!")

  while true:
    let line = await socket.recvLine()
    # TODO: Post to NS once we receive CASReply
    #  asyncCheck socket1.send(message)
    # TODO: Differentiate between NS and CAS
    # Err, why is this incoming line?
    # Why not basic validation before? doable?
    echo(portInt, ": Incoming: ", line)
    # XXX: Hacky to get sender
    if portInt == 6002:
      try:
        var readMsg = parseCASResponse(line)
        echo("readMsg2: ", readMsg)
        # XXX: This should be hit, wy not?
        if readMsg.has(id):
          # XXX: for data, need to map it back
          echo("readMsg id: ", readMsg.id)
        echo("readMsg id regardless:", readMsg.id)
        if readMsg.has(data):
          echo("readMsg data: ", readMsg.data)
      except:
        echo("Ignoring incoming message: " & getCurrentExceptionMsg())

echo("Node started")
# TODO: paramCount and paramStr parsing args
let serverAddr = "localhost"

proc handleInput(input: string) =
  echo("input ", input)
  var request = new CASRequest
  request.operation = CASRequest_Op.POST
  request.data = input
  # XXX: In real-life this would be encrypted
  # XXX: These stream operations seem fishy
  var stream = newStringStream()
  stream.write(request)
  var stringified = $stream.data

  # XXX Why \L?
  let payload = stringified & "\r\L"
  # Can't see encoding but they are here in byte string
  # for c in payload:
  #   echo("payload items: ", c)
  asyncCheck socket2.send(payload)

# XXX: If NS and CAS aren't online these will crash
# This doesn't work, still get error not caught
try:
  # Connect to NS
  asyncCheck connect(socket1, serverAddr, 6001)
  # Connecting to CAS
  asyncCheck connect(socket2, serverAddr, 6002)
except:
  echo("Unable to connect to NS and CAS, quitting")
  quit 0

var messageFlowVar = spawn stdin.readLine()
while true:
  if messageFlowVar.isReady():
    # TODO: create message
    # TODO: Differentiate between CAS and NS messages
    echo("Sending \"", ^messageFlowVar, "\"")

    handleInput(^messageFlowVar)
    messageFlowVar = spawn stdin.readLine()

  asyncdispatch.poll()
