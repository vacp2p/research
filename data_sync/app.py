import networkwhisper, sync, threading, time

# XXX: Ugly constants, should be elsewhere
# TODO: Should be symmetric for a and b
# TODO: Read this in from environment
A_KEYPAIR = "0x57083392b29bdf24512c93cfdf45d38c87d9d882da3918c59f4406445ea976a4"
A_PUBKEY = "0x04d94a1a01872b598c7cdc5aca2358d35eb91cd8a91eaea8da277451bb71d45c0d1eb87a31ea04e32f537e90165c870b3e115a12438c754d507ac75bddd6ecacd5"
B_PUBKEY = "0x04ff921ddf78b5ed4537402f59a150caf9d96a83f2a345a1ddf9df12e99e7778f314c9ca72e8285eb213af84f5a7b01aabb62c67e46657976ded6658e1b9e83c73"

def tick_process(node):
    while True:
        #print("tick")
        node.tick()
        time.sleep(1)

def main():
    # Lets check lunch a bit
    # Then, we can actually append message, and if we recv something print it
    # Then make callable so python app.py <json file or smt>

    # Init node
    whisper_node = networkwhisper.WhisperNodeHelper(A_KEYPAIR)
    node = sync.Node(A_PUBKEY, whisper_node, 'burstyMobile', 'batch')
    # XXX: A bit weird? Or very weird
    node.nodes = [node]
    # XXX: Doesn't make sense, a doesn't have b info
    #node.addPeer(B_PUBKEY, b)
    # Clients should decide policy
    node.share(B_PUBKEY)

    # Start background thread
    thread = threading.Thread(target=tick_process, args=[node])
    thread.daemon = True
    thread.start()

    while True:
        text = input("> ")
        print("You wrote", text)
        rec = sync.new_message_record(text)
        node.append_message(rec)

        node.print_sync_state()

main()

# Ok, can send message
# Now share with these other
# And allow b to run as a proc too
