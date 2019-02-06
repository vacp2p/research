from web3 import Web3, HTTPProvider
from threading import Thread
import time, sys

# Constant
#---------------------------------------------------------------------

#host = 'http://localhost:8545'

# XXX
a_keyPair = "0x57083392b29bdf24512c93cfdf45d38c87d9d882da3918c59f4406445ea976a4"
b_keyPair= "0x7b5c5af9736d9f1773f2020dd0fef0bc3c8aeaf147d2bf41961e766588e086e7"

# Derived, used for addressing
a_pubKey = "0x04d94a1a01872b598c7cdc5aca2358d35eb91cd8a91eaea8da277451bb71d45c0d1eb87a31ea04e32f537e90165c870b3e115a12438c754d507ac75bddd6ecacd5"
b_pubKey = "0x04ff921ddf78b5ed4537402f59a150caf9d96a83f2a345a1ddf9df12e99e7778f314c9ca72e8285eb213af84f5a7b01aabb62c67e46657976ded6658e1b9e83c73"

#(def discovery-topic "0xf8946aac")
topic="0xf8946aac"
#topic = '0x00000000'

# API
#---------------------------------------------------------------------

# XXX: Hacky
def newKeyPair():
    raw_keyPair = web3.shh.newKeyPair()
    keyPair = "0x" + raw_keyPair
    return keyPair

# privateKeyID - String: ID of private (asymmetric) key for message decryption.
def pollFilter(topic, keyPair):
    kId = web3.shh.addPrivateKey(keyPair)
    myFilter = web3.shh.newMessageFilter({'topic': topic,
                                          'privateKeyID': kId})
    myFilter.poll_interval = 600;
    return myFilter

def sendMessage(address_to, topic, msg):
    #print("address_to", address_to)
    web3.shh.post({
        'pubKey': address_to,
        'topic': topic,
        'powTarget': 2.01,
        'powTime': 2,
        'ttl': 10,
        'payload': web3.toHex(text=msg)
    });

def getMessages(myFilter):
    filterID = myFilter.filter_id
    retreived_messages = web3.shh.getMessages(filterID)

    for i in range(0, len(retreived_messages)):
        #print(retreived_messages[i]['payload'])
        print("\nRECV " + retreived_messages[i]['payload'].decode("utf-8"))
        #print(retreived_messages[i])

# Run
#---------------------------------------------------------------------

class Daemon:
    def __init__(self):
        self.id = "x"

    def run(self):
        while True:
            #sendMessage(address_to, topic, "hello")
            getMessages(myFilter)
            #print("tick")
            time.sleep(0.3)

# Args
#---------------------------------------------------------------------

if len(sys.argv) < 2:
    print("Missing argument")
    sys.exit(0)

node = sys.argv[1]

# what
oskar="0x04d94a1a01872b598c7cdc5aca2358d35eb91cd8a91eaea8da277451bb71d45c0d1eb87a31ea04e32f537e90165c870b3e115a12438c754d507ac75bddd6ecacd5"
# contact code
#oskar="0x04cfc3a0f6c1cb824823164603959c639f99680485da2446dc316969faca00421b20dba3996bf99b8b5db7745eace60545a77e54784e91e440aa1af931161de3a6"

if(node == "a"):
    print("a")
    keyPair = a_keyPair
    # XXX: Seems weird, should be b_pubkey?
    address_to = oskar
    #address_to = a_pubKey # Works
    #address_to = b_pubKey
    host = "http://localhost:8500"
elif(node == "b"):
    print("b")
    keyPair = b_keyPair
    address_to = oskar
    #address_to = a_pubKey
    host = "http://localhost:8501"
else:
    print("Unknown node")
    sys.exit(0)


# Connection
#---------------------------------------------------------------------

print("host", host)
web3 = Web3(HTTPProvider(host))
from web3.shh import Shh
Shh.attach(web3, "shh")

#kId = web3.shh.addPrivateKey(keyPair)
#pubKey = web3.shh.getPublicKey(kId)


# A sending messages to B and B then checking

# keyPair used for decryption
print("keyPair for filter", keyPair)
myFilter = pollFilter(topic, keyPair)

print("yo sending")
sendMessage(address_to, topic, "hello")
sendMessage(address_to, topic, "hi also")

# XXX this works, well hell a does
# Separate node?
# XXX: Would expect keypair to be sender and pubkey in sendmsg to b receiver
# Are they flipped somehow?
#myFilter = pollFilter(topic, a_keyPair)
#sendMessage(b_pubKey, topic, "hello b")
#sendMessage(a_pubKey, topic, "hello a")
getMessages(myFilter)

#lol="\[\"~#c4\",\[\"Helloaa\",\"text/plain\",\"~:user-message\",154938955408101,1549389554080,\[\"^ \",\"~:chat-id\",\"0x04d94a1a01872b598c7cdc5aca2358d35eb91cd8a91eaea8da277451bb71d45c0d1eb87a31ea04e32f537e90165c870b3e115a12438c754d507ac75bddd6ecacd5\",\"~:text\",\"Hellbaro\"]]]"

#raw = b'["~#c4",["Test","text/plain","~:user-message",154939130505401,1549391305053,["^ ","~:chat-id","0x04d94a1a01872b598c7cdc5aca2358d35eb91cd8a91eaea8da277451bb71d45c0d1eb87a31ea04e32f537e90165c870b3e115a12438c754d507ac75bddd6ecacd5","~:text","Test"]]]'
#raw = b'["~#c4",["Test2","text/plain","~:user-message",154939130605401,1549391306053,["^ ","~:chat-id","0x04d94a1a01872b598c7cdc5aca2358d35eb91cd8a91eaea8da277451bb71d45c0d1eb87a31ea04e32f537e90165c870b3e115a12438c754d507ac75bddd6ecacd5","~:text","Test2"]]]'

#json = ['~#c4', ['Test', 'text/plain', '~:user-message', 154939130505401, 1549391305053, ['^ ', '~:chat-id', '0x04d94a1a01872b598c7cdc5aca2358d35eb91cd8a91eaea8da277451bb71d45c0d1eb87a31ea04e32f537e90165c870b3e115a12438c754d507ac75bddd6ecacd5', '~:text', 'Test']]]

#import json
#json_str = json.loads(raw.decode('utf-8'))
#print(json_str)

def run():
    while True:
        # lol
        time.sleep(0.5)
        text = input("> ")
        #sendMessage(oskar, topic, lol)
        #test = raw.decode('utf-8')
        print("SEND " + text)
        # Sending to A over discovery topic
        # something wrong here
        sendMessage(a_pubKey, topic, text)
        #sendMessage(oskar, topic, test)
        #sendMessage(a_pubKey, topic, "hello" + text)
        #sendMessage(oskar, topic, "hello" + text)

# Take address_to and filter as args?
#threads = []
#daemon = Thread(target=Daemon().run())
#repl = Thread(target=run())
#threads.append(daemon)
#threads.append(repl)
#daemon.start()
#repl.start()

b = Thread(name='background', target=Daemon().run)
f = Thread(name='foreground', target=run)

b.start()
f.start()


# TODO
# Usage:
# ./whisper a
# => type to send message
# => see incoming messages (poll regularly)

# Vice versa for b

# Then:
# - check discovery topic listen
# - try to get end to end e.g. mobile phone
# - hook up to sync
# - consider subscribe instead?

# Connect to nodes

# listen to public channel all channels?


# Can receive messages from mobile, just not send
