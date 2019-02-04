from web3 import Web3, HTTPProvider
web3 = Web3(HTTPProvider('http://localhost:8545'))
from web3.shh import Shh
Shh.attach(web3, "shh")
import time

# XXX: Seems broken
raw_keyPair = web3.shh.newKeyPair()
keyPair = "0x" + raw_keyPair

kId = web3.shh.addPrivateKey(keyPair)

topic = '0x00000000'

# TODO: Discovery topic or other one, or all
myFilter = web3.shh.newMessageFilter({'topic': topic,
                                      'privateKeyID': kId})
myFilter.poll_interval = 600;
print('keyPair: ' + keyPair)
print('Filter ID: ' + myFilter.filter_id)
print(web3.shh.hasKeyPair(kId))
print('PubKey: ' + web3.shh.getPublicKey(kId))

# Test messages

web3.shh.post({
  'pubKey': web3.shh.getPublicKey(kId),
  'topic': topic,
  'powTarget': 2.01,
  'powTime': 2,
  'ttl': 10,
  'payload': web3.toHex(text="test message :)")
});

web3.shh.post({
  'pubKey': web3.shh.getPublicKey(kId),
  'topic': topic,
  'powTarget': 2.01,
  'powTime': 2,
  'ttl': 10,
  'payload': web3.toHex(text="test hello! :)")
});


# get and send message
# should be same

def getMessages():
    filterID = myFilter.filter_id
    retreived_messages = web3.shh.getMessages(filterID)

    for i in range(0, len(retreived_messages)):
        print(retreived_messages[i]['payload'].decode("utf-8"))
        print(retreived_messages[i])

# getMessages()
