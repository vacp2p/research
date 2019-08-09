import protobuf, streams, strutils

# Define protobuf spec and generate Nim code to use it
const protoSpec = """
syntax = "proto3";

message ExampleMessage {
  int32 number = 1;
  string text = 2;
  SubMessage nested = 3;
  message SubMessage {
    int32 a_field = 1;
  }
}

// Note that some of these are for mocking and might not be part of the spec.

// Assuming only one
message CASPostRequest {
  string data = 1;
}

// Respond with hash for success or error
// TODO: Maybe respond with more
message CASPostResponse {
  string id = 1;
  string data = 2;
}

message CASGetRequest {
  string id = 1;
}

message CASGetResponse {
  string id = 1;
  string data = 2;
}

// TODO: This needs more fleshing out, what data is
message NSPostRequest {
  string data = 1;
}

// Ok or error, how best represent?
// Assume ok
message NSPostResponse {
  string info = 1;
}

// Needs more detail on topic
message NSGetRequest {
  string topic = 1;
}

message NSGetResponse {
  string data = 1;
}

message Testing {
  oneof choice {
    string id = 1;
    string data = 2;
  }
}

// XXX: Best way to deal with GET/POST like this?
// One-of seems ugly, but maybe it's just with this lib?
message CASRequest {
  enum Op {
    GET = 0;
    POST = 1;
  }

  Op operation = 1;
  string id = 2;
  string data = 3;
}
"""
parseProto(protoSpec)


# Example follows:
#--------------------------------------------------------
# Create our message
# var msg = new ExampleMessage
# msg.number = 10
# msg.text = "Hello world"
# msg.nested = initExampleMessage_SubMessage(aField = 100)

# # Write it to a stream
# var stream = newStringStream()
# stream.write msg

# # Read the message from the stream and output the data, if it's all present
# stream.setPosition(0)
# var readMsg = stream.readExampleMessage()
# if readMsg.has(number, text, nested) and readMsg.nested.has(aField):
#   echo readMsg.number
#   echo readMsg.text
#   echo readMsg.nested.aField



# var msg1 = new CASPostRequest
# msg1.data = "hi"

# oneof testing - works
#var test = new Testing
#test.choice = Testing_choice_OneOf(option: 1)
#test.choice.id = "hello"
# Err, also works...
#test.choice.data = "hello"

#var msg2 = new CASRequest
# var stream2 = newStringStream()
# stream2.write msg2
# echo stream2

#msg2.choice[0.data = "hi"



proc test() =
  var msg = new CASRequest
  msg.operation = CASRequest_Op.POST
  msg.data = "testing"
  var stream = newStringStream()
  stream.write msg

  echo("msg ", msg)
#  echo("stream ", stream)

  # Read the message from the stream and output the data, if it's all present
  stream.setPosition(0)
  var readMsg = stream.readCASRequest()
  if readMsg.has(id):
    echo("id ", readMsg.id)
  if readMsg.has(operation) and readMsg.operation == CASRequest_Op.POST:
    echo("operation is a POST", readMsg.operation, readMsg.operation == CASRequest_Op.POST)

  echo("readMsg ", readMsg)

proc test2() =
  # First we create a message
  var msg = new CASRequest
  msg.operation = CASRequest_Op.POST
  msg.data = "testing"
  echo("msg: ", msg)

  # Create a stream and write to it, then stringify dat afield
  var stream = newStringStream()
  stream.write(msg)
  var data = $stream.data
  # XXX: so this works, kind of, but it's just part of it
  # I want "\b\x01\x1A\atesting" not just "testing"
  let req = stream.readAll()

  # Then we stringify it (to send as a line-delimited packet)
  #let req = $msg #& "\r\L"
  echo("req: ", req)

  var stream2 = newStringStream()
  stream2.setPosition(0)
  var readMsg = stream2.readCASRequest()
  echo("readMsg: ", readMsg)
  if readMsg.has(operation):
    echo("operation found")

#test()
#test2()

# fromHex API changed? doesn't compile
#let s = "0x_1235_8df6"
#doAssert fromHex[int](s) == 305499638
