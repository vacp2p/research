# Sync protocol PoC

import hashlib
import networksim
import networkwhisper
import random
import sync_pb2
import time

# Each group belongs to a client.
# Hardcoded for now.
# group\_id = HASH("GROUP\_ID", client\_id, group\_descriptor)
GROUP_ID = "0xdeadbeef"

# TODO: Introduce exponential back-off for send_time based on send_count

# XXX: Hardcoded for logging, cba
#NODE = 'xxx'

# XXX: Add debug log level
#def log(message):
    # XXX: Instead of this, how about printing this to a sync log?
    #print(message)
    # XXX: Don't know which node! Oops.
 #   with open(NODE + 'sync.log', 'w') as f:
  #      f.write(message + '\n')

#    print(message)

def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z

class Node():
    def __init__(self, logfn, name, network, profile, mode='batch'):
        self.name = name
        self.log = []
        self.messages = {}
        self.sync_state = {}
        self.peers = {}
        self.network = network
        self.time = 0
        self.mode = mode
        self.offeredMessages = {} # XXX: Should be bounded
        self.logger = logfn

        # XXX: Assumes only one group
        self.group_id = GROUP_ID
        self.sharing = {GROUP_ID: set()}


        # Network should be aware of sync node so it can call it
        network.sync_node = self

        self.profile = profile
        # for index in pulsating reseries if mobile node

        # XXX: Hacky
        if (self.name == 'A'):
            self.randomSeed = 0
        elif (self.name == 'B'):
            self.randomSeed = 1
        else:
            self.randomSeed = random.randint(1,10)

        if profile == 'burstyMobile':
            self.reliability = 0.1
            self.update_availability()
        elif profile == 'onlineDesktop':
            self.reliability = 1 # or 0.9
        else:
            self.reliability = 1
        self.availability = self.reliability

    def tick(self):
        # XXX: What else do?
        # TODO: Send message if reached send time
        self.time += 1

        if (self.profile == 'burstyMobile'):
            self.update_availability()

        if (self.availability == 1):
            if (self.mode == 'batch'):
                self.ack_sent_messages()
                self.ack_offered_messages()
                self.req_offered_messages()
                self.send_requested_messages()
                self.send_messages()
            elif (self.mode == 'interactive'):
                self.ack_received_messages()
                self.ack_offered_messages()
                self.req_offered_messages()
                self.send_requested_messages()
                self.offer_messages()
        #elif (self.availability == 0):
            #print "*** node NOT available", self.name
        #else:
        #    print "*** conflation overload, reliability/availability mismatch"

    # NOTE: Assuming same semantics for batch and interactive mode.
    #- **Acknowledge** any messages **received** from the peer that the device has
    #not yet acknowledged
    def ack_received_messages(self):
        self.ack_sent_messages()

    # - **Acknowledge** any messages **sent** by the peer that the device has not yet
    #   acknowledged
    def ack_sent_messages(self):
        # TODO: Accumulate and send all in one go

        # XXX: Better Pythonesque way to do this
        for mid, x in self.sync_state.items():
            for peer, flags in x.items():
                if flags['ack_flag'] == 1:
                    ack_rec = new_ack_record([mid])
                    self.network.send_message(self.name, peer, ack_rec)
                    self.sync_state[mid][peer]['ack_flag'] = 0
                    self.logger("    ACK ({} -> {}): {}".format(self.name[-4:], peer[-4:], mid[-4:]))

    # - **Acknowledge** any messages **offered** by the peer that the device holds,
    #   and has not yet acknowledged
    # ACK maybe once?!
    def ack_offered_messages(self):
        for peer, message_ids in self.offeredMessages.items():
            for message_id in message_ids:
                if (message_id in self.messages and
                    # XXX: What if they didn't receive ACK?
                    self.sync_state[message_id][peer]['ack_flag'] == 1):
                    # XXX: Slurp up
                    ack_rec = new_ack_record([message_id])
                    self.sync_state[message_id][peer]['ack_flag'] = 0
                    self.network.send_message(self.name, peer, ack_rec)

    #  **Request** any messages **offered** by the peer that the device does not
    #   hold, and has not yet requested
    # NOTE: (Overloaded?) use of send_time and send_count for reqs.
    # Seems OK since hold flag clarifies if you need to offer/send or ack.
    def req_offered_messages(self):
        # XXX: Not removing from cache, instead letting it grow indefinitely
        # (later: bounded) UNLESS ACK etc is received
        for peer_id, message_ids in self.offeredMessages.items():
            for message_id in message_ids:
                if (message_id not in self.messages and
                    # XXX: Not clear this is part of spec
                    self.sync_state[message_id][peer_id]['send_time'] <= self.time
                    ):
                    # XXX: Slurp up
                    req_rec = new_req_record([message_id])
                    self.network.send_message(self.name, peer_id, req_rec)

                    n = self.sync_state[message_id][peer_id]["send_count"] + 1
                    self.update_sync_state(message_id, peer_id, {
                        'hold_flag': 1,
                        'send_count': n,
                        'send_time': self.time + int(n**2) + 1
                    })

                    self.logger("REQUEST ({} -> {}): {}".format(self.name[-4:], peer_id[-4:], message_id[-4:]))
                    # XXX: It is double requesting, should be polite

    # - **Send** any messages that the device is **sharing** with the peer, that have
    #   been **requested** by the peer, and that have reached their send times
    def send_requested_messages(self):
        for message_id, x in self.sync_state.items():
            for peer_id, flags in x.items():
                if (peer_id in self.sharing[self.group_id] and
                    flags['request_flag'] == 1 and
                    flags['send_time'] <= self.time):
                    message = self.messages[message_id]
                    send_count = self.sync_state[message_id][peer_id]["send_count"] + 1
                    self.sync_state[message_id][peer_id]["send_count"] = send_count
                    self.sync_state[message_id][peer_id]["send_time"] += self.time + send_count*2
                    self.sync_state[message_id][peer_id]["request_flag"] = 0
                    self.logger('MESSAGE ({} -> {}): {} requested and sent'.format(self.name[-4:], peer_id[-4:], message_id[-4:]))
                    # XXX: Can introduce latency here
                    self.network.send_message(self.name, peer_id, message)

    # When turn off request flag?

    #- **Offer** any messages that the device is **sharing** with the peer, and does
    #  not know whether the peer holds, and that have reached their send times
    # XXX: Not tested yet, interactive mode
    def offer_messages(self):
        for message_id, x in self.sync_state.items():
            for peer_id, flags in x.items():
                ids = []
                if (peer_id in self.sharing[self.group_id] and
                    flags['hold_flag'] == 0 and
                    flags['send_time'] <= self.time):
                    # TODO: Extend to slurp up all, need index peer->message
                    offer_rec = new_offer_record([message_id])
                    # HERE we send
                    # XXX: peer_id, should be pbukey
                    self.network.send_message(self.name, peer_id, offer_rec)
                    send_count = self.sync_state[message_id][peer_id]["send_count"] + 1
                    self.sync_state[message_id][peer_id]["send_count"] = send_count
                    self.sync_state[message_id][peer_id]["send_time"] += self.time + send_count*2
                    self.logger("  OFFER ({} -> {}): {}".format(self.name[-4:], peer_id[-4:], message_id[-4:]))

    # - **Send** any messages that the device is **sharing** with the peer, and does
    #   not know whether the peer holds, and that have reached their send times
    def send_messages(self):
        for message_id, x in self.sync_state.items():
            for peer_id, flags in x.items():
                # Should be case for B no?
                if (peer_id in self.sharing[self.group_id] and
                    flags['hold_flag'] == 0 and
                    flags['send_time'] <= self.time):
                    message = self.messages[message_id]
                    send_count = self.sync_state[message_id][peer_id]["send_count"] + 1
                    self.sync_state[message_id][peer_id]["send_count"] = send_count
                    self.sync_state[message_id][peer_id]["send_time"] += self.time + send_count*2
                    self.logger('MESSAGE ({} -> {}): {} sent'.format(self.name[-4:], peer_id[-4:], message_id[-4:]))
                    # XXX: Can introduce latency here
                    self.network.send_message(self.name, peer_id, message)

    # XXX: Why would node know about peer and not just name?
    # TODO: Refactor this to illustrate that it is just a set of pubkeys
    def addPeer(self, peer_id, peer):
        self.peers[peer_id] = peer

    def share(self, peer_id):
        self.sharing[self.group_id].add(peer_id)

    # Helper method
    def update_sync_state(self, message_id, peer_id, new_state):
        if message_id not in self.sync_state:
            self.sync_state[message_id] = {}
        if peer_id not in self.sync_state[message_id]:
            self.sync_state[message_id][peer_id] = {
                "hold_flag": 0,
                "ack_flag": 0,
                "request_flag": 0,
                "send_count": 0,
                "send_time": self.time + 1
            }

        current = self.sync_state[message_id][peer_id]
        new = merge_two_dicts(current, new_state)
        self.sync_state[message_id][peer_id] = new

    def append_message(self, message):
        message_id = get_message_id(message)
        #print("*** append", message)
        self.log.append({"id": message_id,
                         "message": message})
        # XXX: Ugly but easier access while keeping log order
        self.messages[message_id] = message
        self.sync_state[message_id] = {}
        # Ensure added for each peer
        # If we add peer at different time, ensure state init
        # TODO: Only share with certain peers, e.g. clientPolicy
        # XXX here we go, probably
        #print("**SHARE1 SHDNOTBEEMPTY", self.peers)
        # TODO: Problem - this shouldn't be empty
        # Where does this come from?
        for peer in self.peers.keys():
            if peer in self.sharing[self.group_id]:
                #print("**SHARE2", peer)
                # ok, then what?
                self.sync_state[message_id][peer] = {
                    "hold_flag": 0,
                    "ack_flag": 0,
                    "request_flag": 0,
                    "send_count": 0,
                    "send_time": self.time + 1
                }

    # TODO: Probably something more here for message parsing
    # TODO: Need to switch from object to pubkey here with name etc
    def on_receive(self, sender, message):
        if random.random() < self.reliability:
            #print "*** {} received message from {}".format(self.name, sender.name)
            if (message.header.type == 1):
                self.on_receive_message(sender, message)
            elif (message.header.type == 0):
                self.on_receive_ack(sender, message)
            elif (message.header.type == 2):
                self.on_receive_offer(sender, message)
            elif (message.header.type == 3):
                self.on_receive_request(sender, message)
            else:
                print("XXX: unknown message type")
        else:
            self.logger("*** node {} offline, dropping message".format(self.name))

    # TODO: Problem: It assumes there's a name, as opposed to a pubkey
    def on_receive_message(self, sender_pubkey, message):
        message_id = get_message_id(message)
        self.logger('MESSAGE ({} -> {}): {} received'.format(sender_pubkey[-4:], self.name[-4:], message_id[-4:]))
        if message_id not in self.sync_state:
            self.sync_state[message_id] = {}

        if sender_pubkey in self.sync_state[message_id]:
            self.sync_state[message_id][sender_pubkey]['hold_flag'] == 1
            self.sync_state[message_id][sender_pubkey]['ack_flag'] == 1
            # XXX: ACK again here?
        # XXX: This is bad, sender here with Whisper is only pbukey
        self.sync_state[message_id][sender_pubkey] = {
            "hold_flag": 1,
            "ack_flag": 1,
            "request_flag": 0,
            "send_count": 0,
            "send_time": 0
        }

        # XXX: If multiple group id, dispatch per group id
        for peer in self.sharing[self.group_id]:
            if peer not in self.sync_state[message_id]:
                self.sync_state[message_id][peer] = {
                    "hold_flag": 0,
                    "ack_flag": 0,
                    "request_flag": 0,
                    "send_count": 0,
                    "send_time": 0
                }

        self.messages[message_id] = message

    def on_receive_ack(self, sender_pubkey, message):
        for ack in message.payload.ack.id:
            self.logger('    ACK ({} -> {}): {} received'.format(sender_pubkey[-4:], self.name[-4:], ack[-4:]))
            self.sync_state[ack][sender_pubkey]["hold_flag"] = 1

    def on_receive_offer(self, sender_pubkey, message):
        for message_id in message.payload.offer.id:
            self.logger('  OFFER ({} -> {}): {} received'.format(sender_pubkey[-4:], self.name[-4:], message_id[-4:]))
            if (message_id in self.sync_state and
                sender_pubkey in self.sync_state[message_id] and
                self.sync_state[message_id][sender_pubkey]['ack_flag'] == 1):
                print("Have message, not ACKED yet, add to list", sender_pubkey, message_id)
                if sender_pubkey not in self.offeredMessages:
                    self.offeredMessages[sender_pubkey] = []
                self.offeredMessages[sender_pubkey].append(message_id)
            elif message_id not in self.sync_state:
                #print "*** {} on_receive_offer from {} not holding {}".format(self.name, sender_pubkey, message_id)
                if sender_pubkey not in self.offeredMessages:
                    self.offeredMessages[sender_pubkey] = []
                self.offeredMessages[sender_pubkey].append(message_id)
            #else:
            #    print "*** {} on_receive_offer have {} and ACKd OR peer {} unknown".format(self.name, message_id, sender_pubkey)

            # XXX: Init fn to wrap updates
            if message_id not in self.sync_state:
                self.sync_state[message_id] = {}
            if sender_pubkey not in self.sync_state[message_id]:
                self.sync_state[message_id][sender_pubkey] = {
                    "hold_flag": 1,
                    "ack_flag": 0,
                    "request_flag": 0,
                    "send_count": 0,
                    "send_time": 0
                }
            self.sync_state[message_id][sender_pubkey]['hold_flag'] = 1
            #print "*** {} offeredMessages {}".format(self.name, self.offeredMessages)

    def on_receive_request(self, sender_pubkey, message):
        for req in message.payload.request.id:
            self.logger('REQUEST ({} -> {}): {} received'.format(sender_pubkey[-4:], self.name[-4:], req[-4:]))
            self.sync_state[req][sender_pubkey]["request_flag"] = 1

    def print_sync_state(self):
        print("\n{} POV @{}".format(self.name[-4:], self.time))
        print("-" * 60)
        n = self.name
        for message_id, x in self.sync_state.items():
            line = message_id[-4:] + " | "
            for peer, flags in x.items():
                line += peer[-4:] + ": "
                if flags['hold_flag']:
                    line += "hold "
                if flags['ack_flag']:
                    line += "ack "
                if flags['request_flag']:
                    line += "req "
                line += "@" + str(flags['send_time'])
                line += "(" + str(flags['send_count']) + ")"
                line += " | "

            print(line)
        #log("-" * 60)

    # Shorter names for pubkey
    def print_sync_state2(self):
        print("\n{} POV @{}".format(self.name[-4:], self.time))
        print("-" * 60)
        n = self.name[-4:]
        for message_id, x in self.sync_state.items():
            line = message_id[-4:] + " | "
            for peer, flags in x.items():
                line += peer[-4:] + ": "
                if flags['hold_flag']:
                    line += "hold "
                if flags['ack_flag']:
                    line += "ack "
                if flags['request_flag']:
                    line += "req "
                line += "@" + str(flags['send_time'])
                line += "(" + str(flags['send_count']) + ")"
                line += " | "

            print(line)
        #log("-" * 60)

    def update_availability(self):
        #arr = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
        arr = [1, 1, 0, 0, 1, 1, 0, 0]
        idx = (self.time + self.randomSeed) % 8 # 10
        self.reliability = arr[idx]
        # XXX conflating these for now, depends on POV/agency
        self.availability = arr[idx]

# XXX: Self-describing better in practice, format?
def sha1(message):
    # XXX correct encoding?
    sha = hashlib.sha1(message.encode('utf-8'))
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
    s = "MESSAGE_ID" + msg.group_id + str(msg.timestamp) + msg.body.decode()
    #print("***", s)
    return sha1(s)

# TODO: Move these protobuf helpers somewhere better

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
    msg.payload.message.body = str.encode(body)
    return msg

def new_ack_record(ids):
    msg = sync_pb2.Record()
    msg.header.version = 1
    # assert based on type and length
    msg.header.type = 0 # ACK type
    # XXX: Should be inferred
    msg.header.length = 10
    for id in ids:
        msg.payload.ack.id.append(id)
    return msg

def new_offer_record(ids):
    msg = sync_pb2.Record()
    msg.header.version = 1
    # assert based on type and length
    msg.header.type = 2 # OFFER type
    # XXX: Should be inferred
    msg.header.length = 10
    for id in ids:
        msg.payload.offer.id.append(id)
    return msg

def new_req_record(ids):
    msg = sync_pb2.Record()
    msg.header.version = 1
    # assert based on type and length
    msg.header.type = 3 # REQUEST type
    # XXX: Should be inferred
    msg.header.length = 10
    for id in ids:
        msg.payload.request.id.append(id)
    return msg


# Mocking
################################################################################

# TODO: For whisper nodes should be public keys
# What about keypair to try to decrypt? should be in node

def run(steps=10):
    n = networksim.NetworkSimulator()

    # XXX: Not clear to me what's best here
    # Interactive: less BW, Batch: less coordination
    a = Node("A", n, 'burstyMobile', 'batch')
    b = Node("B", n, 'burstyMobile', 'batch')
    c = Node("C", n, 'desktop', 'interactive')
    d = Node("D", n, 'desktop', 'batch')

    n.peers["A"] = a
    n.peers["B"] = b
    n.peers["C"] = c
    n.peers["D"] = d
    n.nodes = [a, b, c, d]

    a.addPeer("B", b)
    a.addPeer("C", c)
    b.addPeer("A", a)
    c.addPeer("A", a)

    #b.addPeer("C", c) # hm
    #c.addPeer("B", b)

    b.addPeer("D", d)
    c.addPeer("D", d)

    # NOTE: Client should decide policy, implict group
    a.share("B")
    b.share("A")

    # C and D participating
    # a.share("C")
    b.share("D")
    c.share("A")
    c.share("D")
    d.share("B")
    d.share("C")

    print("\nAssuming one group context (A-B (C-D) share):")

    # XXX: Conditional append to get message graph?
    # TODO: Actually need to encode graph, client concern
    local_appends = {
        1: [[a, "A: hello world"]],
        2: [[b, "B: hello!"]],
    }

    for i in range(steps):
        # NOTE: include signature and parent message
        if n.time in local_appends:
            for peer, msg in local_appends[n.time]:
                rec = new_message_record(msg)
                peer.append_message(rec)

        n.tick()
        #a.print_sync_state()
        #b.print_sync_state()
        #c.print_sync_state()

    # a.print_sync_state()
    # b.print_sync_state()
    # c.print_sync_state()
    # d.print_sync_state()

def whisperRun(steps=10):
    a_keyPair = "0x57083392b29bdf24512c93cfdf45d38c87d9d882da3918c59f4406445ea976a4"
    b_keyPair= "0x7b5c5af9736d9f1773f2020dd0fef0bc3c8aeaf147d2bf41961e766588e086e7"

    # TODO: should be node names
    # Derived, used for addressing
    a_pubKey = "0x04d94a1a01872b598c7cdc5aca2358d35eb91cd8a91eaea8da277451bb71d45c0d1eb87a31ea04e32f537e90165c870b3e115a12438c754d507ac75bddd6ecacd5"
    b_pubKey = "0x04ff921ddf78b5ed4537402f59a150caf9d96a83f2a345a1ddf9df12e99e7778f314c9ca72e8285eb213af84f5a7b01aabb62c67e46657976ded6658e1b9e83c73"

    aNode = networkwhisper.WhisperNodeHelper(a_keyPair)
    bNode = networkwhisper.WhisperNodeHelper(b_keyPair)

    # XXX: Not clear to me what's best here
    # Interactive: less BW, Batch: less coordination
    a = Node(a_pubKey, aNode, 'burstyMobile', 'batch')
    b = Node(b_pubKey, bNode, 'burstyMobile', 'batch')

    # XXX: Not clear this is needed for Whisper, since all nodes should be part of network
    # Possibly analog with topics?
    #n.peers["A"] = a
    #n.peers["B"] = b
    aNode.nodes = [a]
    bNode.nodes = [b]

    a.addPeer(b_pubKey, b)
    b.addPeer(a_pubKey, a)

    # NOTE: Client should decide policy, implict group
    a.share(b_pubKey)
    b.share(a_pubKey)

    print("\nAssuming one group context (A-B) share):")

    # XXX: Conditional append to get message graph?
    # TODO: Actually need to encode graph, client concern
    local_appends = {
        1: [[a, "A: hello world"]],
        2: [[b, "B: hello!"]],
    }

    # XXX: what is this again? should be for both nodes
    for i in range(steps):
        # NOTE: include signature and parent message
        if aNode.time in local_appends:
            for peer, msg in local_appends[aNode.time]:
                rec = new_message_record(msg)
                peer.append_message(rec)

        # XXX: Why discrete time model here?
        aNode.tick()
        bNode.tick()
        #a.print_sync_state()
        #b.print_sync_state()

    # a.print_sync_state2()
    # b.print_sync_state2()

# TODO: With Whisper branch this one breaks, probably due to sender{,.name} => sender_pubkey mismatch.
#run(30)
#whisperRun(30)
