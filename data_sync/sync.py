# Sync protocol PoC

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
