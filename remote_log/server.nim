import net, os

var server: Socket  = newSocket()

proc handler() {.noconv.} =
  stdout.write("Shutting down server.")

  # Unclear if this matters with ReuseAddr
  server.close()

  quit 0

setControlCHook(handler)

server.setSockOpt(OptReuseAddr, true)
server.bindAddr(Port(1234))
server.listen()
stdout.writeLine("Server started, listening to new connections on port 1234")

var client: Socket
var address = ""

server.accept(client)
stdout.writeLine("Server: client connected")

while true:

  let message: string = client.recvLine()

  if message == "":
    break

  stdout.writeLine("Server: received from client: ", message)

server.close()
