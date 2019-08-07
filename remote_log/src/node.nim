import net, os, threadpool, asyncdispatch, asyncnet

var socket = newAsyncSocket()

proc handler() {.noconv.} =
  stdout.writeLine("Shutting down connection.")
  socket.close()
  quit 0

setControlCHook(handler)

proc connect(socket: AsyncSocket, serverAddr: string) {.async.} =
  echo("Connecting to ", serverAddr)
  await socket.connect(serverAddr, 6001.Port)
  echo("Connected!")

  while true:
    let line = await socket.recvLine()
    # TODO: parse message
    echo("Incoming: ", line)

echo("Node started")
# TODO: paramCount and paramStr parsing args
let serverAddr = "localhost"
asyncCheck connect(socket, serverAddr)
var messageFlowVar = spawn stdin.readLine()
while true:
  if messageFlowVar.isReady():
    # TODO: create message
    #echo("Sending \"", ^messageFlowVar, "\"")
    let message = ^messageFlowVar & "\r\L"
    asyncCheck socket.send(message)
    messageFlowVar = spawn stdin.readLine()

  asyncdispatch.poll()

# 1) Node wants to post data to ns, and ns stores it
# 2) Node can recevive

# Since we want to use CAS update result to do NS update,
# Having sending and receiving behavior in same proc seems desirable
# Also easier to reason about, so let's do that

# To do encoding we probably want something like protobuf, or maybe use hacky
# stringify if that's a thing, or JSON

# Consider separating out interactive parts into client.nim
