import protobuf, streams

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
"""
parseProto(protoSpec)


# Example follows:
#--------------------------------------------------------
# Create our message
var msg = new ExampleMessage
msg.number = 10
msg.text = "Hello world"
msg.nested = initExampleMessage_SubMessage(aField = 100)

# Write it to a stream
var stream = newStringStream()
stream.write msg

# Read the message from the stream and output the data, if it's all present
stream.setPosition(0)
var readMsg = stream.readExampleMessage()
if readMsg.has(number, text, nested) and readMsg.nested.has(aField):
  echo readMsg.number
  echo readMsg.text
  echo readMsg.nested.aField
