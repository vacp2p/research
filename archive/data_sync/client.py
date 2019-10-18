# Interpreting messages, etc

# TODO: Expand message to be a payload with message hash
# TODO: Encode group with message graph and immutable messages

# NOTE: does nothing right now

# Should build up message graph and display

# What does a message look like, roughly:
ex = {'payload': "hello_world",
      'content-type': "text/plain",
      'signed_sender': 'A-signed-pubkey',
      'dependencies': ["foo_message_id"]}

# TODO: Move to client
# XXX: This confuses things somewhat, as this is
# client concerns
#acc = "\n"
#for _, msg in a.messages.items():
#    acc += msg.payload.message.body + "\n"
## XXX: Where is the sender stored? in msg?
#print "A POV:", acc

#acc = "\n"
#for _, msg in b.messages.items():
#    acc += msg.payload.message.body + "\n"
#print "B POV:", acc
## TODO: Encode things like client, group scope, etc
# client\_id = R(HASH\_LEN)
CLIENT_ID = "0xdeadbeef"

class TestClient():
    def __init__(self):
        self.client_id = "0xdeadbeef"


    # NOTE: Client should decide policy, implict group
#    a.share("B")
#    b.share("A")

