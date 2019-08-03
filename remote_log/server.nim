import net, os, nativesockets

var server: Socket  = newSocket()

proc handler() {.noconv.} =
  stdout.write("Shutting down server.")

  # Unclear if this matters with ReuseAddr
  server.close()

  quit 0

setControlCHook(handler)

server.setSockOpt(OptReuseAddr, true)
server.getFd().setBlocking(false)
server.bindAddr(Port(1234))
server.listen()
stdout.writeLine("Server started, listening to new connections on port 1234")

var clients: seq[Socket] = @[]

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

      stdout.writeLine("Server: received from client: ", message)
    except TimeoutError:
      discard

  for index in clientsToRemove:
    clients.del(index)
    stdout.writeLine("Server: client disconnected")

server.close()
