# Sync protocol PoC

import hashlib
import sync_pb2
import time

# TODO: Expand message to be a payload with message hash
# TODO: Add support for multiple peers
# TODO: Introduce latency and unreliability
# TODO: send_time should be time
# TODO: Use .proto files

def log(message):
    print message

class Node():
    def __init__(self, name):
        self.name = name
        self.log = []
        self.sync_state = {}
        self.peers = {}

    def append_message(self, message):
        message_id = get_message_id(message)
        self.log.append({"id": message_id,
                         "message": message})
        self.sync_state[message_id] = {"hold_flag": 0,
                                       "ack_flag": 0,
                                       "request_flag": 0,
                                       "send_count": 0,
                                       "send_time": 0}

    def send_message(self, peer_id, message):
        message_id = get_message_id(message)
        peer = self.peers[peer_id]
        # TODO: Use peer to update sync_state
        self.sync_state[message_id]["send_count"] = 1
        self.sync_state[message_id]["send_time"] = 1

        log('MESSAGE ({} -> {})'.format(self.name, peer.name))

        # XXX: Tightly coupled
        peer.receive_message(self.name, message)

    def receive_message(self, sender, message):
        print "received message", sender, get_message_id(message)
        # Should be of certain type
        # TODO: Acknowledge message
        # Generate ack message

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
    #print s
    return sha1(s)

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

# Mocking
################################################################################

# Create nodes
a = Node("A")
b = Node("B")

# Add as sharing nodes
# NOTE: Assumes just one sharing context
a.peers["B"] = b
b.peers["A"] = a

# NOTE: For proof of concept this is simply a text field
# More realistic example would include sender signature, and parent message ids
a0 = new_message_record("hello world")

# Local append
a.append_message(a0)

# TODO: send_message should be based on send_time
a.send_message("B", a0)

# TODO: Use the actual protobufs

# need to be bytes
acks = sync_pb2.Record()
acks.header.version = 1
# XXX: not showing up if version is 0
acks.header.type = 0
acks.header.length = 10
acks.payload.ack.id.extend(["a", "b"])

print "*** Sync state before receive:"
print "A", a.sync_state
print "B", b.sync_state
