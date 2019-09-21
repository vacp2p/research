import net, os

let client = newSocket()

proc handler() {.noconv.} =
  stdout.writeLine("Shutting down connection.")
  client.close()
  quit 0

setControlCHook(handler)

client.connect("127.0.0.1", Port(1234))
stdout.writeLine("Client connected to server on 127.0.0.1:1234")

while true:
  stdout.write("> ")
  let message: string = stdin.readLine()
  client.send(message & "\r\L")

client.close()
