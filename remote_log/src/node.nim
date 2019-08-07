import net, os, threadpool, asyncdispatch, asyncnet, strutils

var socket1 = newAsyncSocket()
var socket2 = newAsyncSocket()

proc handler() {.noconv.} =
  stdout.writeLine("Shutting down connection.")
  socket1.close()
  socket2.close()
  quit 0

setControlCHook(handler)

proc isNSMessage(message: string): bool =
  return message.split(' ')[0] == "NS"

proc isCASMessage(message: string): bool =
  return message.split(' ')[0] == "CAS"

# XXX: drop first part? or maybe you know, use proper encoding
# XXX: Crashes if bad too, obv
proc prepareMessage(message: string): string =
  var s = ""
  try:
    s = message.split(' ')[1] & " :" & message.split(':')[1]
  except:
    echo("prepareMessage error ", message)
    s = "bad msg"
  return s

assert("NS POST :hi".split(' ')[0] == "NS")
var test = "NS POST :foo bar"
assert(test.split(' ')[1] & " :" & test.split(':')[1] == "POST :foo bar")
assert isNSMessage("NS POST :hi")
assert prepareMessage("NS POST :foo bar") == "POST :foo bar"

proc connect(socket: AsyncSocket, serverAddr: string, portInt: int) {.async.} =
  echo("Connecting to ", serverAddr, ":", portInt)
  await socket.connect(serverAddr, portInt.Port)
  echo(portInt, ": Connected!")

  while true:
    let line = await socket.recvLine()
    # TODO: parse message
    # TODO: Differentiate between NS and CAS
    echo(portInt, ": Incoming: ", line)

echo("Node started")
# TODO: paramCount and paramStr parsing args
let serverAddr = "localhost"

# Connect to NS
asyncCheck connect(socket1, serverAddr, 6001)

# Connecting to CAS
asyncCheck connect(socket2, serverAddr, 6002)

var messageFlowVar = spawn stdin.readLine()
while true:
  if messageFlowVar.isReady():
    # TODO: create message
    # TODO: Differentiate between CAS and NS messages
    echo("Sending \"", ^messageFlowVar, "\"")

    let prepared = prepareMessage(^messageFlowVar)
    let message = prepared & "\r\L"

    if isNSMessage(^messageFlowVar):
      echo("Send NS: ", prepared)
      asyncCheck socket1.send(message)
    elif isCASMessage(^messageFlowVar):
      echo("Send CAS: ", prepared)
      asyncCheck socket2.send(message)
    else:
      echo("Unknown message type ", ^messageFlowVar)

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

# Send message triggers:
# Upload to cas => get id
# Upload to NS
# So other node can fetch

# Interface here?
# Two connections

# CAS and NS different how?
