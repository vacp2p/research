# Sync protocol PoC

import hashlib
import sync_pb2
import time

# TODO: Expand message to be a payload with message hash
# TODO: Introduce latency and unreliability
# TODO: send_time should be time
# TODO: Use .proto files

# Lets expand with multiple peers

def log(message):
    print message

# NOTE: Inspired by github.com/ethereum/research networksim.py.
class NetworkSimulator():
    def __init__(self):
        self.nodes = []
        self.time = 0
        self.queue = {}
        self.peers = {}

    def tick(self):
        if self.time in self.queue:
            # XXX: Should sender be here?
            for sender, receiver, msg in self.queue[self.time]:
                # NOTE: Assumes 100% reliability
                receiver.on_receive(sender, msg)
        # Discrete time model
        print "tick", self.time
        for n in self.nodes:
            n.tick()
        self.time += 1

    # NOTE: Direct message, no broadcast etc
    def send_message(self, sender_id, receiver_id, message):
        # XXX: Assuming sender exists
        sender = self.peers[sender_id]
        receiver = self.peers[receiver_id]
        recv_time = self.time + 1
        if recv_time not in self.queue:
            self.queue[recv_time] = []
        self.queue[recv_time].append((sender, receiver, message))

class Node():
    def __init__(self, name, network):
        self.name = name
        self.log = []
        self.sync_state = {}
        self.peers = {}
        self.network = network
        self.time = 0

    def tick(self):
        # XXX: What else do?
        # TODO: Send message if reached send time
        self.time += 1

    def append_message(self, message):
        message_id = get_message_id(message)
        self.log.append({"id": message_id,
                         "message": message})
        self.sync_state[message_id] = {}
        # XXX: For each peer
        # Ensure added for each peer
        # If we add peer at different time, ensure state init
        for peer in self.peers.keys():
            self.sync_state[message_id][peer] = {"hold_flag": 0,
                                                 "ack_flag": 0,
                                                 "request_flag": 0,
                                                 "send_count": 0,
                                                 "send_time": 0}

    def send_message(self, peer_id, message):
        message_id = get_message_id(message)
        peer = self.peers[peer_id]
        # XXX: Use tick clock for this
        self.sync_state[message_id][peer_id]["send_count"] = 1
        self.sync_state[message_id][peer_id]["send_time"] = 1

        log('MESSAGE ({} -> {}): {}'.format(self.name, peer.name, message_id))

        # XXX: Can introduce latency here
        self.network.send_message(self.name, peer_id, message)

    def on_receive(self, sender, message):
        if (message.header.type == 1):
            self.on_receive_message(sender, message)
        elif (message.header.type == 0):
            self.on_receive_ack(sender, message)
        else:
            print "XXX: unknown message type"

    def on_receive_message(self, sender, message):
        message_id = get_message_id(message)
        # Message coming from A
        if message_id not in self.sync_state:
            self.sync_state[message_id] = {}
        self.sync_state[message_id][sender.name] = {
            "hold_flag": 1,
            "ack_flag": 0,
            "request_flag": 0,
            "send_count": 0,
            "send_time": 0
        }

        # XXX How is this sent?
        ack_rec = new_ack_record(message_id)
        self.network.send_message(self.name, sender.name, ack_rec)
        log("ACK ({} -> {}): {}".format(self.name, sender.name, message_id))

    def on_receive_ack(self, sender, message):
        for ack in message.payload.ack.id:
            self.sync_state[ack][sender.name]["hold_flag"] = 1

    def print_sync_state(self):
        #log("{}'s view of .other peer".format(self.name))
        #log("---------------------------")
        n = self.name
        for message_id, x in self.sync_state.items():
            for peer, flags in x.items():
                m = message_id[:4]
                r = flags['request_flag']
                h = flags['hold_flag']
                a = flags['ack_flag']
                c = flags['send_count']
                t = flags['send_time']
                log("{}(view of {}): {} | hold={} req={} ack={} time={} count={}".format(n, peer, m, h, r, a, t, c))
                #log("---------------------------")


# XXX: Self-describing better in practice, format?
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

# XXX: Only takes one id
def new_ack_record(id):
    msg = sync_pb2.Record()
    msg.header.version = 1
    # assert based on type and length
    msg.header.type = 0 # ACK type
    # XXX: Should be inferred
    msg.header.length = 10
    msg.payload.ack.id.append(id)
    return msg

# Mocking
################################################################################

print "\n"

n = NetworkSimulator()

# Create nodes
a = Node("A", n)
b = Node("B", n)
c = Node("C", n) # Passive node?

# XXX: Want names as pubkey sender
n.peers["A"] = a
n.peers["B"] = b
n.peers["C"] = c
n.nodes = [a, b, c]

# Add as sharing nodes
# NOTE: Assumes just one sharing context
a.peers["B"] = b
a.peers["C"] = c
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

n.tick()
a.print_sync_state()
b.print_sync_state()

n.tick()
a.print_sync_state()
b.print_sync_state()

n.tick()
a.print_sync_state()
b.print_sync_state()



print "\n"
