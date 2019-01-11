import random

# NOTE: Inspired by github.com/ethereum/research networksim.py.
class NetworkSimulator():
    def __init__(self):
        self.nodes = []
        self.time = 0
        self.queue = {}
        self.peers = {}
        # Global network reliability
        self.reliability = 1 # 0.95? Dunno.

    def tick(self):
        if self.time in self.queue:
            # XXX: Should sender be here?
            for sender, receiver, msg in self.queue[self.time]:
                if random.random() < self.reliability:
                    #print "*** message ok", sender.name, "->", receiver.name
                    receiver.on_receive(sender, msg)
                #else:
                    #print "*** message dropped", sender.name, "->", receiver.name
        #print ""
        print "tick", self.time + 1
        #print "-----------"
        for n in self.nodes:
            n.tick()
        self.time += 1

    # XXX: This should be normal distribution or Poisson
    def latency_uniform_random(self):
        # XXX: Hardcode for now, easier analyze
        latency = 1
        #latency = random.randint(1,3)
        return latency

    # NOTE: Direct message, no broadcast etc
    def send_message(self, sender_id, receiver_id, message):
        #print "*** (network) send_message", sender_id, receiver_id
        # XXX: Assuming sender exists
        sender = self.peers[sender_id]
        receiver = self.peers[receiver_id]
        recv_time = self.time + self.latency_uniform_random()
        if recv_time not in self.queue:
            self.queue[recv_time] = []
        self.queue[recv_time].append((sender, receiver, message))
