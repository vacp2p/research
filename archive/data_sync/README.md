# BSP-spec

Goal: a Protobuf spec of https://code.briarproject.org/briar/briar-spec/blob/master/protocols/BSP.md

As well as some PoC around it.

Initial PoC report: https://notes.status.im/THYDMxSmSSiM5ASdl-syZg

## Setup

```
# ensure you have protobuf-compiler, python3, pip installed
# Using virtualenv
python3 -m pip install --user virtualenv
python3 -m virtualenv env
source env/bin/activate
pip install web3 protobuf

make

#make run # see sync.py
# or:
python3 app.py <a|b>
```

## Whisper

Run geth node:
```
geth --testnet --syncmode=light --ws --wsport=8546 --wsaddr=localhost --wsorigins=statusjs --rpc --maxpeers=25 --shh --shh.pow=0.002 --wsapi=eth,web3,net,shh,debug,admin,personal
```
geth --testnet --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 
```
geth --testnet --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8500 --datadir=/tmp/foo --port=30000
geth --testnet --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=/tmp/bar --port=30001


- add nodes to connect

- running whisper node on own nodes?

cp static-nodes.json ~/.ethereum/testnet/geth/

# send 1:1 chat

0x04cfc3a0f6c1cb824823164603959c639f99680485da2446dc316969faca00421b20dba3996bf99b8b5db7745eace60545a77e54784e91e440aa1af931161de3a6

geth --testnet --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=/tmp/bar --port=30001 --ipcpath /tmp/bar.ipc

geth --testnet --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=~/.ethereum/node-b --port=30001


## Setup
This assumes:
```
cp static-nodes.json ~/.ethereum/node-a/
cp static-nodes.json ~/.ethereum/node-b/
```

FIXME: toml config?

```
WARN [02-21|03:27:02.567] Found deprecated node list file /tmp/node-b/static-nodes.json, please use the TOML config file instead.
```


TODO: Consider lowering PoW, but am I even connected to each other?
Can manually hack I guess - what is my enode?

ERROR[02-21|03:28:18.982] bad envelope received, peer will be disconnected peer=57c24fba33c13642 err="envelope with low PoW received: PoW=0.001908, hash=[0x44651a153e4b9d6e8080c35fb81c28f9586c842e28d3e15809b2ef01725e0f3d]"


Manual A and B, into static-nodes?
#enode://01acca361b49bdf611a8ce3f39beaac712bdfefa0d552f25fc7c54217a9e678a9233f0b1622d0c489ff022f7a6ad7387203d45edc000edbf066ff246d35d5e1a@127.0.0.1:30000

#enode://421a707a09d9ff08028fd9e47df876bd4cfbd873ce12cfe00702b068acf077518c5c065fb94b61782287695e276973edfa0361c81227d2e7c0570deedfbe7dbb@127.0.0.1:30001



Ok, not working. Trying to add peer but no luck
admin.addPeer("enode://01acca361b49bdf611a8ce3f39beaac712bdfefa0d552f25fc7c54217a9e678a9233f0b1622d0c489ff022f7a6ad7387203d45edc000edbf066ff246d35d5e1a@127.0.0.1:30000")

# IF same node, then what?


geth --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=~/.ethereum/node-b --port=30001 attach
Welcome to the Geth JavaScript console!

for (var p=0; p < admin.peers.length; p++) { console.log(admin.peers[p].enode); }

admin.addPeer("enode://531e252ec966b7e83f5538c19bf1cde7381cc7949026a6e499b6e998e695751aadf26d4c98d5a4eabfb7cefd31c3c88d600a775f14ed5781520a88ecd25da3c6@35.225.227.79:30504")


ok, so this works.

Problem: even with detailed logs very little feedback


If I cal lwith al lthis sync node etc no worky
geth --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=~/.ethereum/node-b --port=30001 --vmodule eth/*=2,p2p=4,shh=5,whisper=5 &> node-b.log

ANd addpeer




## Gethy

How to start:
```
geth --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=~/.ethereum/node-b --port=30001 --vmodule eth/*=2,p2p=4,shh=5,whisper=5 &> node-b.log
```

or use scripts, look in folder.

```
./scripts/start-node-b.sh &> node-b.log &
```

How to attach:
```
 geth --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=~/.ethereum/node-b --port=30001 attach
```


admin.addPeer("enode://421a707a09d9ff08028fd9e47df876bd4cfbd873ce12cfe00702b068acf077518c5c065fb94b61782287695e276973dfa0361c81227d2e7c0570deedfbe7dbb@127.0.0.1:30001");
admin.addPeer("enode://421a707a09d9ff08028fd9e47df876bd4cfbd873ce12cfe00702b068acf077518c5c065fb94b61782287695e276973edfa0361c81227d2e7c0570deedfbe7dbb@127.0.0.1:30001");

admin.addPeer("enode://e8b7716c2a972a18f3ef31831fe3c2f8f584e59a877d73eca3ac50581ee94a5ec732bdab33db14e260be8093193eb6c777a0980ab341c3bde0256853ddc07bf5@127.0.0.1:30000");


And if I restart node it disconnects previous ones...

Why?
enode://421a707a09d9ff08028fd9e47df876bd4cfbd873ce12cfe00702b068acf077518c5c065fb94b61782287695e276973edfa0361c81227d2e7c0570deedfbe7dbb@127.0.0.1:44984

geth      7053 user   68u  IPv6 141618      0t0  TCP localhost:30000->localhost:44984 (ESTABLISHED)
geth      7415 user   63u  IPv4 141044      0t0  TCP localhost:44984->localhost:30000 (ESTABLISHED)

## Next steps

- End to end add several notes

- Sanity check wrt adding peers manually etc

- Figure out latency smaller