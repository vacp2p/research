# BSP-spec

Goal: a Protobuf spec of https://code.briarproject.org/briar/briar-spec/blob/master/protocols/BSP.md

As well as some PoC around it.

Initial PoC report: https://notes.status.im/THYDMxSmSSiM5ASdl-syZg

```
make
make run # see sync.py
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
