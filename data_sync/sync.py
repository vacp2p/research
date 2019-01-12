# Sync protocol PoC

import hashlib
import networksim
import random
import sync_pb2
import time

# Each group belongs to a client.
# Hardcoded for now.
# group\_id = HASH("GROUP\_ID", client\_id, group\_descriptor)
GROUP_ID = "0xdeadbeef"

# TODO: Introduce exponential back-off for send_time based on send_count

# XXX: Add debug log level
def log(message):
    print message

class Node():
    def __init__(self, name, network, profile, mode='batch'):
        self.name = name
        self.log = []
        self.messages = {}
        self.sync_state = {}
        self.peers = {}
        self.network = network
        self.time = 0
        self.mode = mode
        self.offeredMessages = {} # XXX: Should be bounded

        # XXX: Assumes only one group
        self.group_id = GROUP_ID
        self.sharing = {GROUP_ID: set()}

        self.profile = profile
        # for index in pulsating reseries if mobile node

        # XXX: Hacky
        if (self.name == 'A'):
            self.randomSeed = 0
        elif (self.name == 'B'):
            self.randomSeed = 5
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
                    log("    ACK ({} -> {}): {}".format(self.name, peer, mid[:4]))

    # - **Acknowledge** any messages **offered** by the peer that the device holds,
    #   and has not yet acknowledged
    def ack_offered_messages(self):
        for peer, message_ids in self.offeredMessages.items():
            for message_id in message_ids:
                if message_id in self.messages:
                    # XXX: Slurp up
                    ack_rec = new_ack_record([message_id])
                    self.network.send_message(self.name, peer, ack_rec)


    #  **Request** any messages **offered** by the peer that the device does not
    #   hold, and has not yet requested
    # XXX: If you do this every tick, that's a problem no? "Not yet requested"
    # No logic for backoff, and atm not a bounded list
    # If A thinks C is req, wy not resend?
    # TODO: Consider logic for request back-off
    def req_offered_messages(self):
        # XXX: Not removing from cache, instead letting it grow indefinitely
        # (later: bounded) UNLESS ACK etc is received
        for peer, message_ids in self.offeredMessages.items():
            for message_id in message_ids:
                if message_id not in self.messages:
                    # XXX: Slurp up
                    req_rec = new_req_record([message_id])
                    self.network.send_message(self.name, peer, req_rec)
                    log("REQUEST ({} -> {}): {}".format(self.name, peer, message_id[:4]))
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
                    self.sync_state[message_id][peer_id]["send_count"] += 1
                    self.sync_state[message_id][peer_id]["send_time"] += 2
                    # Huh?
                    self.sync_state[message_id][peer_id]["request_flag"] = 0
                    # XXX: Bug, says C req flag is set, shouldn't be
                    print "XXX", self.sync_state[message_id][peer_id]

                    log('MESSAGE ({} -> {}): {} requested and sent'.format(self.name, peer_id, message_id [:4]))
                    # XXX: Can introduce latency here
                    self.network.send_message(self.name, peer_id, message)

    # When turn off request flag?

    # Three above requires OFFER functionality
    # Interactive mode

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
                    self.network.send_message(self.name, peer_id, offer_rec)
                    self.sync_state[message_id][peer_id]["send_count"] += 1
                    self.sync_state[message_id][peer_id]["send_time"] += 2
                    log("  OFFER ({} -> {}): {}".format(self.name, peer_id, message_id[:4]))

    # - **Send** any messages that the device is **sharing** with the peer, and does
    #   not know whether the peer holds, and that have reached their send times
    def send_messages(self):
        for message_id, x in self.sync_state.items():
            for peer_id, flags in x.items():
                if (peer_id in self.sharing[self.group_id] and
                    flags['hold_flag'] == 0 and
                    flags['send_time'] <= self.time):
                    message = self.messages[message_id]
                    self.sync_state[message_id][peer_id]["send_count"] += 1
                    self.sync_state[message_id][peer_id]["send_time"] += 2
                    log('MESSAGE ({} -> {}): {} sent'.format(self.name, peer_id, message_id [:4]))
                    # XXX: Can introduce latency here
                    self.network.send_message(self.name, peer_id, message)

    # XXX: Why would node know about peer and not just name?
    def addPeer(self, peer_id, peer):
        self.peers[peer_id] = peer

    def share(self, peer_id):
        self.sharing[self.group_id].add(peer_id)

    def append_message(self, message):
        #print "*** append_message", self.name
        message_id = get_message_id(message)
        self.log.append({"id": message_id,
                         "message": message})
        # XXX: Ugly but easier access while keeping log order
        self.messages[message_id] = message
        self.sync_state[message_id] = {}
        # XXX: For each peer
        # Ensure added for each peer
        # If we add peer at different time, ensure state init
        # TODO: Only share with certain peers, e.g. clientPolicy
        for peer in self.peers.keys():
            if peer in self.sharing[self.group_id]:
                self.sync_state[message_id][peer] = {
                    "hold_flag": 0,
                    "ack_flag": 0,
                    "request_flag": 0,
                    "send_count": 0,
                    "send_time": self.time + 1
                    }

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
                print "XXX: unknown message type"
        else:
            log("*** node {} offline, dropping message".format(self.name))

    def on_receive_message(self, sender, message):
        message_id = get_message_id(message)
        log('MESSAGE ({} -> {}): {} received'.format(sender.name, self.name, message_id[:4]))
        if message_id not in self.sync_state:
            self.sync_state[message_id] = {}
        self.sync_state[message_id][sender.name] = {
            "hold_flag": 1,
            "ack_flag": 1,
            "request_flag": 0,
            "send_count": 0,
            "send_time": 0
        }

        self.messages[message_id] = message

    def on_receive_ack(self, sender, message):
        for ack in message.payload.ack.id:
            log('    ACK ({} -> {}): {} received'.format(sender.name, self.name, ack[:4]))
            self.sync_state[ack][sender.name]["hold_flag"] = 1

    def on_receive_offer(self, sender, message):
        for message_id in message.payload.offer.id:
            log('  OFFER ({} -> {}): {} received'.format(sender.name, self.name, message_id[:4]))
            if (message_id in self.sync_state and
                sender.name in self.sync_state[message_id] and
                self.sync_state[message_id][sender.name]['ack_flag'] == 1):
                print "Have message, not ACKED yet, add to list", sender.name, message_id
                if sender.name not in self.offeredMessages:
                    self.offeredMessages[sender.name] = []
                self.offeredMessages[sender.name].append(message_id)
            elif message_id not in self.sync_state:
                #print "*** {} on_receive_offer from {} not holding {}".format(self.name, sender.name, message_id)
                if sender.name not in self.offeredMessages:
                    self.offeredMessages[sender.name] = []
                self.offeredMessages[sender.name].append(message_id)
            #else:
            #    print "*** {} on_receive_offer have {} and ACKd OR peer {} unknown".format(self.name, message_id, sender.name)

            # XXX: Init fn to wrap updates
            if message_id not in self.sync_state:
                self.sync_state[message_id] = {}
            if sender.name not in self.sync_state[message_id]:
                self.sync_state[message_id][sender.name] = {
                    "hold_flag": 1,
                    "ack_flag": 0,
                    "request_flag": 0,
                    "send_count": 0,
                    "send_time": 0
                }
            self.sync_state[message_id][sender.name]['hold_flag'] = 1
            #print "*** {} offeredMessages {}".format(self.name, self.offeredMessages)

    def on_receive_request(self, sender, message):
        for req in message.payload.request.id:
            log('REQUEST ({} -> {}): {} received'.format(sender.name, self.name, req[:4]))
            self.sync_state[req][sender.name]["request_flag"] = 1

    def print_sync_state(self):
        log("\n{} POV @{}".format(self.name, self.time))
        log("-" * 60)
        n = self.name
        for message_id, x in self.sync_state.items():
            line = message_id[:4] + " | "
            for peer, flags in x.items():
                line += peer + ": "
                if flags['hold_flag']:
                    line += "hold "
                if flags['ack_flag']:
                    line += "ack "
                if flags['request_flag']:
                    line += "req "
                line += "@" + str(flags['send_time'])
                line += "(" + str(flags['send_count']) + ")"
                line += " | "

            log(line)
        #log("-" * 60)

    def update_availability(self):
        arr = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
        idx = (self.time + self.randomSeed) % 10
        self.reliability = arr[idx]
        # XXX conflating these for now, depends on POV/agency
        self.availability = arr[idx]

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
    msg.payload.message.body = body
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

def run(steps=10):
    n = networksim.NetworkSimulator()

    a = Node("A", n, 'burstyMobile', 'interactive')
    b = Node("B", n, 'burstyMobile', 'interactive')
    c = Node("C", n, 'desktop', 'interactive')

    n.peers["A"] = a
    n.peers["B"] = b
    n.peers["C"] = c
    n.nodes = [a, b, c]

    a.addPeer("B", b)
    a.addPeer("C", c)
    b.addPeer("A", a)
    c.addPeer("A", a)

    # NOTE: Client should decide policy, implict group
    a.share("B")
    b.share("A")

    # XXX: Hm, a lot of coordination here? Weird?
    a.share("C")
    b.share("C")
    c.share("A")
    c.share("B")

    print "\nAssuming one group context (A-B-C share):"

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

    a.print_sync_state()
    b.print_sync_state()
    c.print_sync_state()

## TODO: Sync modes, interactive (+bw -latency) and batch (v.v.)

# Need to encode logic for actions taken at given time,
# respect send_time etc,
# WRT offer messages and so on

# Batch mode first (less coordination):
# - **Acknowledge** any messages **sent** by the peer that the device has not yet
#   acknowledged
# - **Acknowledge** any messages **offered** by the peer that the device holds,
#   and has not yet acknowledged
# - **Request** any messages **offered** by the peer that the device does not
#   hold, and has not yet requested
# - **Send** any messages that the device is **sharing** with the peer, that have
#   been **requested** by the peer, and that have reached their send times
# - **Send** any messages that the device is **sharing** with the peer, and does
#   not know whether the peer holds, and that have reached their send times

# each tick
# SEND messages device is SHARING with the peer, doesn't know if peer holds,
# and reached send time
# What mean by sharing

# Member of a group:
# Two peers sync group message they share group
# Membership and sharing dynamic

# How do we de determine if two peers synchronize a
# specific group's messages with eachother?

# For any given (data) group, a device can decide
# if they want to share or not with a peer.

# TODO: ACK should also be share policy
# XXX: Encode offline mostly

# XXX: How does B look at the message?

# XXX: If A,B reliability 0.1 and C 0.9
# How does that actually realistically look?

# Need to encode the other actions and offer etc
# Exponential backoff too probably

# Then C can offer messages to B, e.g.

# How viz message graph?
# XXX: How will C receive the message from A to B?
# TODO: Requires offering to B, e.g.
# Or B requesting it

# Why is A sending same message to C over again
# and again, with reliability = 1,1?
# C no op? it acks but A ignores it?
# Duh, C sends but A doesn't see it...

# TODO: When A comes online, whenever that is
# It needs to requests messages
# Aka ask C (or whomever) for messages
# How?
# - **Request** any messages **offered** by the peer that the device does not
# But how would it know to offer messages?
# It could play nice and offer all messages it has to C, but if C has all
# There needs to be some way for C to go for it, unless A is going to over-offer with bloom filter or so
# Look into this a bit more, naive way is signal

run(20)


# XXX: What happens if ACK fails? Offer back? Lol. See no mention of re-send acks
