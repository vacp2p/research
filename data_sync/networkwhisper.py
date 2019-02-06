from web3 import Web3, HTTPProvider
from web3.shh import Shh
import random

# XXX use these
a_keyPair = "0x57083392b29bdf24512c93cfdf45d38c87d9d882da3918c59f4406445ea976a4"
b_keyPair= "0x7b5c5af9736d9f1773f2020dd0fef0bc3c8aeaf147d2bf41961e766588e086e7"

# Derived, used for addressing
a_pubKey = "0x04d94a1a01872b598c7cdc5aca2358d35eb91cd8a91eaea8da277451bb71d45c0d1eb87a31ea04e32f537e90165c870b3e115a12438c754d507ac75bddd6ecacd5"
b_pubKey = "0x04ff921ddf78b5ed4537402f59a150caf9d96a83f2a345a1ddf9df12e99e7778f314c9ca72e8285eb213af84f5a7b01aabb62c67e46657976ded6658e1b9e83c73"


# XXX: This assumes a node is actually running - shell out to boot geth?
# At least error if proc not running
class WhisperNodeHelper():
    def __init__(self):
        # XXX: Whisper specific, but this host should be unique per node
        self.host = "http://localhost:8500"
        web3 = Web3(HTTPProvider(host))
        Shh.attach(web3, "shh")

        self.topic="0xf8946aac" # discovery-topic

        self.keyPair = "XXX"
        self.myFilter = self.pollFilter(self.topic, self.keyPair)

        # XXX: Prune this
        self.nodes = []
        self.time = 0
        self.queue = {}
        self.peers = {}
        # Global network reliability
        self.reliability = 1 # 0.95? Dunno.

    def poll_filter(self, topic, keyPair):
        # XXX: Doesn't belong here
        kId = web3.shh.addPrivateKey(keyPair)
        pubKey = web3.shh.getPublicKey(kId)
        #print("***PUBKEY", pubKey)
        myFilter = web3.shh.newMessageFilter({'topic': topic,
                                              'privateKeyID': kId})
        # Purpose of this if we do getMessages?
        myFilter.poll_interval = 600;
        return myFilter

    def tick(self):
        myFilter = "XXX"
        filterID = myFilter.filter_id
        retreived_messages = web3.shh.getMessages(filterID)

        # TODO: Deal with these messages similar to simulation
        # receiver.on_receive(sender, msg)
        for i in range(0, len(retreived_messages)):
            #print(retreived_messages[i]['payload'])
            print("\nRECV " + retreived_messages[i]['payload'].decode("utf-8"))
            #print(retreived_messages[i])
        #print ""
        print("tick", self.time + 1)
        #print "-----------"
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
        topic = self.topic
        web3.shh.post({
            'pubKey': address_to,
            'topic': topic,
            'powTarget': 2.01,
            'powTime': 2,
            'ttl': 10,
            'payload': web3.toHex(text=msg)
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



