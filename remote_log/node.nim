import net, os, threadpool

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
  #let message: string = stdin.readLine()
  let message = spawn stdin.readLine()
  echo("Sending \"", ^message, "\"")
  client.send(^message & "\r\L")

client.close()

# 1) Node wants to post data to ns, and ns stores it
# 2) Node can recevive

# Since we want to use CAS update result to do NS update,
# Having sending and receiving behavior in same proc seems desirable
# Also easier to reason about, so let's do that

# To do encoding we probably want something like protobuf, or maybe use hacky
# stringify if that's a thing, or JSON

# Consider separating out interactive parts into client.nim
