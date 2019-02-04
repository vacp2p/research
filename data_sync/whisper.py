from web3 import shh
from web3 import HTTPProvider, Web3
from web3.personal import Personal

status_host = 'http://127.0.0.1:8545'

# XXX: Hardcoded
privatekey = "0x633f01b2b607d4e777db626d876d04613decb5145ec7faeae3e57bf8f008c994"

connect = Web3(HTTPProvider(status_host))
print('connect status ===> ', connect.isConnected())

ms = shh.Shh(connect)
print('info ===>>>> ', ms.info)

id = ms.addPrivateKey(key=privatekey)
print('id ===>>>> ', id)

user_address = ms.getPublicKey(id)
print('user_address ===>>> ', user_address)

privkey = ms.getPrivateKey(id)
print("privkey => ", privkey)

# XXX
topic = Web3.toHex(b'AAAA')
print("topic => ", topic)
text = 'test message'

# XXX
address_to = '0x0487be55c072702a0e4da72158a7432281e8c26aca9501cd0bfeea726dc85f2611e96884e8fc4807c95c04c04af3387b83350a27cc18b96c37543e0f9a41ae47b5'

mes_send = ms.post(
    {
        'ttl': 20,
        'payload': Web3.toHex(text=text),
        'pubKey': address_to,
        'topic': topic,
        'powTarget': 2.5,
        'powTime': 2,
    }
)

if mes_send == True:
    print('Status message => Send')
else:
    print('Message not send')

# TODO: Create a listener
