# Sync protocol PoC

import hashlib
import sync_pb2
import time

# TODO: Expand message to be a payload with message hash
# TODO: Add support for multiple peers
# TODO: Introduce latency and unreliability
# TODO: send_time should be time
# TODO: Use .proto files

class Node():
    def __init__(self, name):
        self.name = name
        self.log = []
        self.sync_state = {}
        self.peers = {}

    def append_message(self, message):
        self.log.append(message)
        self.sync_state[message] = {"hold_flag": 0,
                                    "ack_flag": 0,
                                    "request_flag": 0,
                                    "send_count": 0,
                                    "send_time": 0}

    def send_message(self, peer, message):
        # TODO: Use peer to update sync_state
        self.sync_state[message]["send_count"] = 1
        self.sync_state[message]["send_time"] = 1

        # XXX: Tightly coupled
        receiver = self.peers[peer]
        receiver.receive_message(self.name, message)

    def receive_message(self, sender, message):
        print "received message", sender, message
        # Should be of certain type
        # TODO: Acknowledge message

# Mock

a = Node("A")
b = Node("B")

a.peers["B"] = b
b.peers["A"] = a

a.append_message("a0")

# TODO: send_message should be based on send_time
a.send_message("B", "a0")
print a.sync_state["a0"]

# TODO: Use the actual protobufs

# this is a record
# XXX: where is the message id?
def new_message_record(body):
    msg = sync_pb2.Record()
    msg.header.version = 1
    # assert based on type and length
    msg.header.type = 1 # MESSAGE type
    # XXX: Should be inferred
    msg.header.length = 10
    # XXX: Hardcoded for now
    msg.payload.message.group_id = "foo"
    # XXX: Should be 64 bit integer ms
    msg.payload.message.timestamp = int(time.time())
    msg.payload.message.body = body
    return msg

# need to be bytes
acks = sync_pb2.Record()
acks.header.version = 1
# XXX: not showing up if version is 0
acks.header.type = 0
acks.header.length = 10
acks.payload.ack.id.extend(["a", "b"])

# XXX: Where do we use this?
def sha1(message):
    sha = hashlib.sha1(message)
    return sha.hexdigest()

#- message\_id = HASH("MESSAGE\_ID", group\_id, timestamp, message\_body)

# TODO: Create a message

def create_message(body):
    group_id = "0xdeadbeef"
    timestamp = time.time()
    message_body = body
    message = {"group_id": group_id, "timestamp": timestamp, "message_body": message_body}
    return message

# XXX: Is this hashing correctly?
def get_message_id(message_record):
    msg = message_record.payload.message
    s = "MESSAGE_ID" + msg.group_id + str(msg.timestamp) + msg.body
    print s
    return sha1(s)

# So... a message doesn't have anything pertaining to where it came from?
# Signatures etc but be inside the body payload
foo = new_message_record("hello world")
foo_id = get_message_id(foo)
