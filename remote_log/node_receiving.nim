import net, os

let client = newSocket()

proc handler() {.noconv.} =
  stdout.writeLine("Shutting down connection.")
  client.close()
  quit 0

setControlCHook(handler)

client.connect("127.0.0.1", Port(6001))
stdout.writeLine("Client connected to name service on 127.0.0.1:6001")

while true:
  let receivedMessage: string = client.recvLine()
  stdout.writeLine("Message: ", receivedMessage)

client.close()
