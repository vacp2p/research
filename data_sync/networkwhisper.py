from web3 import Web3, HTTPProvider
from web3.shh import Shh
import random

# Temp
import sync_pb2

# XXX: This assumes a node is actually running - shell out to boot geth?
# At least error if proc not running
class WhisperNodeHelper():
    def __init__(self, keypair):
        # XXX: Whisper specific, but this host should be unique per node
        self.host = "http://localhost:8500"
        self.web3 = Web3(HTTPProvider(self.host))
        Shh.attach(self.web3, "shh")

        self.topic="0xf8946aac" # discovery-topic

        self.keyPair = keypair
        # XXX: Doesn't belong here
        self.kId = self.web3.shh.addPrivateKey(self.keyPair)
        self.myFilter = self.poll_filter(self.topic, self.keyPair)

        # XXX: Prune this
        self.nodes = []
        self.time = 0
        #self.queue = {}
        #self.peers = {}
        # Global network reliability
        self.reliability = 1 # 0.95? Dunno.

    def poll_filter(self, topic, keyPair):
        # XXX: Doesn't belong here
        #kId = self.web3.shh.addPrivateKey(keyPair)
        pubKey = self.web3.shh.getPublicKey(self.kId)
        #print("***PUBKEY", pubKey)
        myFilter = self.web3.shh.newMessageFilter({'topic': topic,
                                                   'privateKeyID': self.kId})
        # Purpose of this if we do getMessages?
        myFilter.poll_interval = 600;
        return myFilter
    def tick(self):
        filterID = self.myFilter.filter_id
        retreived_messages = self.web3.shh.getMessages(filterID)

        # TODO: Deal with these messages similar to simulation
        # receiver.on_receive(sender, msg)
        for i in range(0, len(retreived_messages)):
            #print(retreived_messages[i]['payload'])
            #print("\nRECV TYPE", type(retreived_messages[i]['payload']))

            # XXX: This parsing should probably happen elsewhere
            msg = sync_pb2.Record()
            #full = retreived_messages[i]
            sig = retreived_messages[i]['sig']
            print("***SIG", sig.hex())
            payload = retreived_messages[i]['payload']
            #print("\nRECV payload", payload)
            msg.ParseFromString(payload)
            print("\nRECV parsed", msg)
            # XXX correct way to refer to MESSAGE
            if msg.header.type == 1:
                print("\nRECV parse", msg.payload.message.body.decode())

            # XXX Only one receiver, this is a node not network
            receiver = self.nodes[0]
            # HEREATM
            # How sender?
            # TODO: Figure out how we know sender, assumes signed message
            # inside payload? but if it isn't your own message then how work
            # How does this currently work? How do we know from who it is?
            # chat-id seems to be pubkey and some stuff
            # sohuld be in signature sig

            sender = sig.hex()
            receiver.on_receive(sender, msg)

        #print ""
        print("tick", self.time + 1)
        #print "-----------"

        # XXX: This is ugly, why is this ticking nodes?
        # NOTE: Only self is ticking
        for n in self.nodes:
            n.tick()
        self.time += 1

    # NetworkSim stub
    # def tick(self):
    #     if self.time in self.queue:
    #         # XXX: Should sender be here?
    #         for sender, receiver, msg in self.queue[self.time]:
    #             if random.random() < self.reliability:
    #                 #print "*** message ok", sender.name, "->", receiver.name
    #                 receiver.on_receive(sender, msg)
    #             #else:
    #                 #print "*** message dropped", sender.name, "->", receiver.name
    #     #print ""
    #     print "tick", self.time + 1
    #     #print "-----------"
    #     for n in self.nodes:
    #         n.tick()
    #     self.time += 1

    # sender id / pubkey not needed for now
    # topic assumed to be hardcoded
    def send_message(self, sender_id, address_to, msg):
        print("*** (whisper-network) send_message", address_to)
        # XXX: Is this what we want to do?
        payload = msg.SerializeToString()
        print("*** (whisper-network) send_message payload", payload)
        #print("*** (whisper-network) send_message hex", self.web3.toHex(payload))
        topic = self.topic
        self.web3.shh.post({
            'pubKey': address_to,
            'topic': topic,
            'powTarget': 2.01,
            'powTime': 2,
            'ttl': 10,
            'sig': self.kId,
            'payload': self.web3.toHex(payload)
        });

    # NetworkSim stub
    # def send_message(self, sender_id, receiver_id, message):
    #     #print "*** (network) send_message", sender_id, receiver_id
    #     # XXX: Assuming sender exists
    #     sender = self.peers[sender_id]
    #     receiver = self.peers[receiver_id]
    #     recv_time = self.time + self.latency_uniform_random()
    #     if recv_time not in self.queue:
    #         self.queue[recv_time] = []
    #     self.queue[recv_time].append((sender, receiver, message))

    # XXX: This should be normal distribution or Poisson
    # NetworkSim stub; not needed for Whisper probably
    # def latency_uniform_random(self):
    #     # XXX: Hardcode for now, easier analyze
    #     latency = 1
    #     #latency = random.randint(1,3)
    #    return latency



