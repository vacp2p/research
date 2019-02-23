#!/usr/bin/env sh

# Should probably be a subprocess in python and print to some logger
# Or Docker compose or whatever.

#cp static-nodes.json /tmp/node-b/

echo "[Starting node-b...]"

echo "[Copying static-nodes...]"
cp static-nodes.json ~/.ethereum/node-b/
#geth --testnet --syncmode=light --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=~/.ethereum/node-b --port=30001 --verbosity=4

echo "[geth starting at port 30001, see node-b.log for logs.]"
geth --rpc --maxpeers=25 --shh --shh.pow=0.002 --rpcport=8501 --datadir=~/.ethereum/node-b --port=30001 --vmodule eth/*=2,p2p=4,shh=5,whisper=5 #&> node-b.log
