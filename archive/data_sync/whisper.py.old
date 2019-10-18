from web3 import shh
from web3 import HTTPProvider, Web3
from web3.personal import Personal
import time

# Run geth repo with <OPTIONS>
# Ensure there's a private key ~
# Pubkey
# 0x040cb9373bf8cd9dcbca4b75ccbfad52bbc66d1aaca8095adb2a7dcf8504146f0abde4ca22adf77b5062f113585befbf37e06dcadd0ce1093695e53d00d2109528

# XXX: Message not sent, due to threads?

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
#topic = Web3.toHex(b'AAAA')
topic = '0x00000000'
print("topic => ", topic)
text = 'test message'

# XXX
#address_to = '0x0487be55c072702a0e4da72158a7432281e8c26aca9501cd0bfeea726dc85f2611e96884e8fc4807c95c04c04af3387b83350a27cc18b96c37543e0f9a41ae47b5'

# Copy pasted
address_to = '0x04bbfb9fbe8239c2fb1895511f306d731c283ba3070d8642d4fbb4da1e4923454b8de6d82b671a4787c8e24d2cf2cf947d6da5ff6d12bf7147d1c0c5d2acbaf8ba'

# nice works

# address too is who?
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

# How check status?
print(mes_send)
