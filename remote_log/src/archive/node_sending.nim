import net, os

let client = newSocket()

proc handler() {.noconv.} =
  stdout.writeLine("Shutting down connection.")
  client.close()
  quit 0

setControlCHook(handler)

client.connect("127.0.0.1", Port(6001))
stdout.writeLine("Client connected to name service on 127.0.0.1:6001")

# TODO: Rewrite this to be async so it can send/recv at same time
while true:
  stdout.write("> ")
  let message: string = stdin.readLine()
  client.send(message & "\r\L")

client.close()
